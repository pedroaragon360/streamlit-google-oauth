import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import requests
import json  # Import the json module

import openai
import uuid
import time
import pandas as pd
import io
import re
import base64
from openai import OpenAI
import mimetypes

if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_pass" not in st.session_state:
    st.session_state.user_pass = None
    
st.set_page_config(
    page_title="The Valley ChatGPT",
    page_icon="",
    layout="wide")
st.markdown('<style> [data-testid=stToolbar]{ top:-10em } </style>', unsafe_allow_html=True)

def historial(data):    
    if data["id"] not in st.session_state.savedMessages:
        if data["role"] == 'assistant':
            st.session_state["disabled"] = False
        st.session_state.savedMessages.append(data["id"])
        response = requests.post("https://thevalley.es/lms/gpt_app/historial.php", data=data)
        
def authTHV(data):
    response = requests.post("https://thevalley.es/lms/gpt_app/auth.php", data=data)
    return response.text
def getThreads(data):
    st.session_state.threads = json.loads(requests.post("https://thevalley.es/lms/gpt_app/threads.php", data=data).text)
    
st.markdown('<div id="logoth" style="z-index: 9999999; background: url(https://thevalley.es/lms/gpt_app/logow.png);  width: 200px;  height: 27px;  position: fixed;  background-repeat: no-repeat;  background-size: auto 100%;  top: 1.1em;  left: 1em;"></div>', unsafe_allow_html=True)

# Define the OAuth2 scopes
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'  # Include the 'openid' scope
]


def login(femail,fpass):
    if requests.post("https://thevalley.es/lms/gpt_app/login.php", data={'email': femail, 'pass': fpass}).text == "1":
        st.session_state.authed = 1
        st.session_state.user_info = femail

query_params = st.experimental_get_query_params()
if 'email' in query_params and 'pass' in query_params:
    login(query_params["email"][0], query_params["pass"][0])
    st.session_state.user_email = query_params["email"][0]
    st.session_state.user_pass = query_params["pass"][0]
    
# Function to initialize the flow object with client ID and secret from Streamlit secrets
def init_flow():
    return Flow.from_client_config(
        client_config={
            "web": {
                "client_id": st.secrets['GOOGLE_CLIENT_ID'],
                "client_secret": st.secrets['GOOGLE_CLIENT_SECRET'],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [st.secrets['REDIRECT_URI']],
                "scopes": SCOPES
            }
        },
        scopes=SCOPES,
        redirect_uri=st.secrets['REDIRECT_URI']
    )

# Streamlit app layout
def main():
    flow = init_flow()

    # Check for the code parameter in the URL query parameters
    query_params = st.experimental_get_query_params()
    if 'code' in query_params:
        try:
            # Complete the authentication process
            flow.fetch_token(code=query_params['code'][0])
            credentials = flow.credentials
            st.session_state['credentials'] = credentials.to_json()
        except Exception as e:
            # Handle exceptions and display an error message or redirect to login
            st.error("Vuelve a iniciar sesión")
            
    if 'credentials' not in st.session_state:
        # Display login screen
        st.title("The Valley ChatGPT")
        st.markdown('<span style="display: block;font-size: 0.5em; ">Powered by <img src="https://thevalley.es/lms/gpt_app/logogpt.png" style="margin-left:0.2em" height="20"></span>', unsafe_allow_html=True)
        st.markdown("Bienvenido a la aplicación GPT-4 de OpenAI ofrecido por The Valley.\n Esta aplicación es gratuita para uso educativo.")
        auth_url, _ = flow.authorization_url(prompt='consent')


        with st.form("login"):
            #st.write("Soy Alumno")
            femail = st.text_input('Email', key='campoemail', value=st.session_state.user_email, autocomplete="on")
            fpass = st.text_input('Clave', key='campopass', type='password', value=st.session_state.user_pass, autocomplete="on")
            # Every form must have a submit button.
            submitted = st.form_submit_button("Entrar  >",type = "primary")
            if submitted:
                if requests.post("https://thevalley.es/lms/gpt_app/login.php", data={'email': femail, 'pass': fpass}).text == "1":
                    params = {
                        "email": femail,
                        "pass": fpass
                    }
                    st.experimental_set_query_params(**params)
                    st.toast("Login " + femail + " " + fpass)
                    st.session_state.authed = True
                    st.session_state.user_info = femail
                    #query_params = st.experimental_get_query_params()
                    st.rerun()
                else:
                    st.error("Login incorrecto, inténtalo de nuevo")
        col1, col2 = st.columns(2)        
        with col1:
            st.caption("¿Actualmente estás cursando un programa y quieres acceso?")
            st.link_button("Solicita acceso >", f'{auth_url}')
        with col2:
            st.caption("¿Eres docente o empleado?")
            st.link_button("Acceso interno >", f'{auth_url}')
        st.stop()
    else:
        # # User is authenticated, show the content screen
        # st.title("Welcome to the App")
        # # Convert JSON string back to dictionary
        credentials_dict = json.loads(st.session_state['credentials'])
        credentials = Credentials.from_authorized_user_info(credentials_dict)
        
        # Make a request to Google's user info endpoint
        userinfo_response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {credentials.token}'}
        )
        
        st.session_state.user_info = userinfo_response.json().get('email', '-')
        checkAuth = authTHV({"user":st.session_state.user_info})
        if checkAuth != "1":
            st.title("Subscripción no activa")
            st.write("No tienes acceso actualmente a esta aplicación. \n Si estás cursando un programa en estos momentos, solicita tu alta escribiendo a altagpt@thevalley.es")
            st.stop()
            
        #st.write(f"User info: {st.session_state.user_info}")
        # st.write("")


# Run the app
if __name__ == "__main__" and "authed" not in st.session_state:
    main()


# Initialize OpenAI client
client = OpenAI()

# Your chosen model
MODEL = "gpt-4-1106-preview"

# Initialize session state variables
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "run" not in st.session_state:
    st.session_state.run = {"status": None}
# if "currentChatRole" not in st.session_state: # evitamos mostrar varias veces el rol cuando se reciben varios mensajes 
#     st.session_state.currentChatRole = 'user' 
if "messages" not in st.session_state:
    st.session_state.messages = []
if "savedMessages" not in st.session_state:
    st.session_state.savedMessages = []
if "retry_error" not in st.session_state:
    st.session_state.retry_error = 0
if "authed" not in st.session_state:
    st.session_state.authed = 1
if "preloadThread" not in st.session_state:
    st.session_state.preloadThread = False
if "messages_progress" not in st.session_state:
    st.session_state.messages_progress = []
# Set up the page
#st.set_page_config(page_title="Asistente")


#st.sidebar.markdown("Por Pedro Aragón", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([":speech_balloon: Conversación", ":paperclip: Sube un fichero", "Historial", "Reportar error", "Preguntas frecuentes"])

st.markdown('<style>[data-baseweb=tab-list] {   position: fixed !important; top: 0.5em;   left: 11em;   z-index: 9999999; } </style>', unsafe_allow_html=True)

# Initialize session state for the uploader key
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

# File uploader for CSV, XLS, XLSX
with tab2:
    st.caption("Tamaño máximo 3MB. Formatos soportados: PDF, CSV, XLS, XLSX, JSON")
    uploaded_file = st.file_uploader("", type=["csv", "xls", "json", "xlsx", "pdf"], key=f'file_uploader_{st.session_state.uploader_key}')

with tab1:
    with st.chat_message('assistant'):
        st.caption('Esta aplicación está disponible para uso educativo, úsalo con responsabilidad. Tu actividad queda guardada en "Historial".')
        st.write('¡Hola! Soy el asistente GPT de The Valley. ¿cómo te puedo ayudar?')
        
# Initialize OpenAI assistant
if "assistant" not in st.session_state:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    try:
        st.session_state.assistant = openai.beta.assistants.retrieve(st.secrets["OPENAI_ASSISTANT"])
        # Your code that might raise an error
        if "thread_id" in query_params:
            st.session_state.thread = client.beta.threads.retrieve(query_params["thread_id"][0])    
            st.session_state.preloadThread = True
        else:
            st.session_state.thread = client.beta.threads.create(
                metadata={'session_id': st.session_state.session_id}
            )
    except Exception as e:
        # Handling the error
        st.warning(f"Error: {e}")
        # Optionally, re-raise the error if you want to propagate it further
        raise

# Display chat messages
if (hasattr(st.session_state.run, 'status') and st.session_state.run.status == "completed") or st.session_state.preloadThread == True:

    st.session_state.messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread.id
    )
    for message in reversed(st.session_state.messages.data):
        if message.role in ["user", "assistant"]:
            with tab1:
                with st.chat_message(message.role):
                    for content_part in message.content:
                        if message.role == 'assistant':
                            run_steps = client.beta.threads.runs.steps.list(thread_id=st.session_state.thread.id,run_id=message.run_id  )
                            #st.write(run_steps.data)
                            for steps in reversed(run_steps.data):
                                if hasattr(steps.step_details, 'tool_calls'):
                                    with st.expander("Código generado por Code Interpreter"):
                                        #st.write(steps.step_details)
                                        st.code(steps.step_details.tool_calls[0].code_interpreter.input)
                                        if "outputs" in steps.step_details.tool_calls[0].code_interpreter:
                                            st.subheader("Output del código")
                                            st.text(steps.step_details.tool_calls[0].code_interpreter.outputs[0].logs)
                                    
                    #if steps.tools[0].type == 'code_interpreter':
                        # Handle text content
                        if hasattr(content_part, 'text') and content_part.text:
                            message_text = content_part.text.value
                            pattern = r'\[.*?\]\(sandbox:.*?\)'
                            #message_text = message_text.replace("\n", "\n\n")
                            message_text = re.sub(pattern, '', message_text)
                            st.markdown(message_text)
                            historial({"user":st.session_state.user_info,"thread":st.session_state.thread.id,"role": message.role, "message": message_text, "id": message.id})
                            #st.write("Msg:", message)
    
                            # Check for and display image from annotations
                            if content_part.text.annotations:
                                for annotation in content_part.text.annotations:
                                    if hasattr(annotation, 'file_path') and annotation.file_path:
                                        file_id = annotation.file_path.file_id
                                        # Retrieve the image content using the file ID
                                        file_name = client.files.retrieve(file_id).filename #eg. /mnt/data/archivo.json
                                        response = client.files.with_raw_response.retrieve_content(file_id)
                                        if response.status_code == 200:
                                            b64_image = base64.b64encode(response.content).decode()
                                        
                                            # Guess the MIME type of the file based on its extension
                                            mime_type, _ = mimetypes.guess_type(file_name)
                                            if mime_type is None:
                                                mime_type = "application/octet-stream"  # Default for unknown types
                                        
                                            # Extract just the filename from the path
                                            filename = file_name.split('/')[-1]
                                        
                                            # Create a download button with the correct MIME type and filename
                                            href = f'<a style="border: 1px solid white;background: white; color: black; padding: 0.4em 0.8em; border-radius: 1em;" href="data:{mime_type};base64,{b64_image}" download="{filename}">Descargar {filename}</a>'
                                            st.markdown(href, unsafe_allow_html=True)
                                            historial({"user":st.session_state.user_info,"thread":st.session_state.thread.id,"role": message.role, "message": href, "id": message.id})
                                        else:
                                            st.error("Failed to retrieve file")
                                        
                        # Handle direct image content
                        if hasattr(content_part, 'image') and content_part.image:
                            image_url = content_part.image.url
                            st.write("IMG API Response:", content_part.image)
                    # Check for image file and retrieve the file ID
                        if hasattr(content_part, 'image_file') and content_part.image_file:
                            image_file_id = content_part.image_file.file_id
                            # Retrieve the image content using the file ID
                            response = client.files.with_raw_response.retrieve_content(image_file_id)
                            if response.status_code == 200:
                                st.image(response.content)
                                b64_image = base64.b64encode(response.content).decode()
                                historial({"user":st.session_state.user_info,"thread":st.session_state.thread.id,"role": message.role, "message": '<img src="data:image/png;base64,'+b64_image+'">', "id": message.id})
                            else:
                                st.error("Failed to retrieve image")

                    

if "disabled" not in st.session_state:
    st.session_state["disabled"] = False

def disable():
    st.session_state["disabled"] = True

if prompt := st.chat_input("¿Cómo te puedo ayudar?", disabled=st.session_state.disabled, on_submit =disable):
    prompt_raw=prompt
    #prompt = prompt.replace("\n", "\n\n")
    if "file_id" in st.session_state and "file_name" in st.session_state:
    #     prompt_raw = "Renombra el archivo " + str(st.session_state.file_id) + " por " + str(st.session_state.file_name) + ". " + prompt_raw
        prompt_raw = f"Acabo de subir el archivo {st.session_state.file_id} en formato {st.session_state.file_format}\n\n{prompt_raw}"
    message_data = {
        "thread_id": st.session_state.thread.id,
        "role": "user",
        "content": prompt_raw
    }
    with tab1:
        with st.chat_message('user'):
            st.markdown(prompt)
            
    # Include file ID in the request if available
    if "file_id" in st.session_state:
        message_data["file_ids"] = [st.session_state.file_id]
        st.session_state.pop('file_id')
    
    st.session_state.messages = client.beta.threads.messages.create(**message_data)

    st.session_state.run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread.id,
        assistant_id=st.session_state.assistant.id,
    )
    st.write('<img src="https://thevalley.es/lms/i/load.gif" height="28px"> Pensando...' if st.session_state.run.status == 'queued' else '', unsafe_allow_html=True)

    if st.session_state.retry_error < 3:
        time.sleep(4)
        st.rerun()
        
if uploaded_file is not None:
    file_type = uploaded_file.type
    try:
        if file_type == "text/csv":
            df = pd.read_csv(uploaded_file)
            df = df.iloc[:200, :15]
            json_str = df.to_csv(index=False)
            file_stream = io.BytesIO(json_str.encode())
            file_type = 'text/csv'
            uploaded_file.name = 'file.csv'

        elif file_type in ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
            df = pd.read_excel(uploaded_file)
            df = df.iloc[:200, :15]
            json_str = df.to_csv(index=False)
            file_stream = io.BytesIO(json_str.encode())
            file_type = 'text/csv'
            uploaded_file.name = 'file.csv'

        elif file_type == "application/pdf":
            file_stream = io.BytesIO(uploaded_file.read())

        else:
            raise ValueError("Formato de archivo no soportado")
            
        file_response = client.files.create(file=file_stream, purpose='assistants')

        # file_stream = uploaded_file.getvalue()
        # file_response = client.files.create(file=file_stream, purpose='assistants')
        st.session_state.file_id = file_response.id
        st.session_state.file_format = file_type
        st.session_state.file_name = uploaded_file.name
        with tab2:
            st.success(f"Archivo subido. File ID: {file_response.id}")
            historial({"user":st.session_state.user_info,"thread":st.session_state.thread.id,"role": 'user', "message": f"Archivo subido: {uploaded_file.name} ID: {file_response.id}", "id": file_response.id})
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(uploaded_file.name)
        if mime_type is None:
            mime_type = "application/octet-stream"  # Default for unknown types
    
        # Create download button
        with tab2:
            st.download_button(
                label="Descargar fichero subido",
                data=file_stream,
                file_name=uploaded_file.name,
                mime=mime_type
            )

        # Reset the uploader by changing the key
        st.session_state.uploader_key += 1
       
    except Exception as e:
        st.error(f"An error occurred: {e}")
                
with tab3: 
    # Parse the JSON string to a Python list
    getThreads({"user":st.session_state.user_info})
    # Iterate over the list and display each thread
    if 'threads' in st.session_state and st.session_state.threads:
        for fecha, thread in st.session_state.threads.items():
            st.link_button(":speech_balloon: Conversación " + str(fecha), "https://thevalley.es/lms/gpt_app/thread_"+str(thread),  use_container_width=True)

def handle_submission(input_value):
    # Process the input value here
    historial({"user":st.session_state.user_info,"thread":st.session_state.thread.id,"role": 'bug', "message": input_value, "id": input_value})
    st.success("¡Gracias! Feedback enviado")

with tab4:
    # Create a text input box
    st.title("¿Algún problema? Envíanos tu feedback")
    input_text = st.text_input("¿Qué problema has tenido en esta conversación?")
    submit_button = st.button("Dar feedback >")
    if submit_button:
        handle_submission(input_text)
        

with tab5:
    if "faq" not in st.session_state:
        response = requests.get("https://thevalley.es/lms/gpt_app/faq.php")
        
        # Convert response to JSON
        if response.status_code == 200:
            faq_data = response.json()  # Convert to Python object (list of lists)
            
            # Store in session state
            st.session_state.faq = faq_data

            # Iterate over each question-answer pair
            for item in faq_data:
                question, answer = item
                with st.expander(f"**{question}**"):
                    st.markdown(answer)
        else:
            st.error("Failed to fetch FAQ data2")

# Handle run status
if hasattr(st.session_state.run, 'status'):

    if st.session_state.run.status == "failed":
        st.toast("Failed")
        st.session_state.retry_error += 1
        with st.chat_message('assistant'):
            if hasattr(st.session_state.run, 'last_error'):
                st.toast("Error:" + st.session_state.run.last_error.message)
                st.write("Atención: " + st.session_state.run.last_error.message)
            if st.session_state.retry_error < 3:
                st.write("Intentándolo de nuevo ......")
                time.sleep(4)
                st.rerun()
            else:
                st.error("Lo sentimos, no se ha podido procesar: " + st.session_state.run.last_error.message)

    elif st.session_state.run.status != "completed":
        st.toast("Not completed")
        st.session_state.run = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread.id,
            run_id=st.session_state.run.id,
        )
        
        run_steps_loading = client.beta.threads.runs.steps.list(thread_id=st.session_state.thread.id,run_id=st.session_state.run.id  )
        #st.write(run_steps_loading.data)
        for steps_loading in reversed(run_steps_loading.data):
            if hasattr(steps_loading.step_details, 'message_creation'):
                st.toast("Mensaje recibido de progreso!")
                messageid = steps_loading.step_details.message_creation.message_id
                if messageid not in st.session_state.messages_progress:
                    message = client.beta.threads.messages.retrieve(message_id = messageid, thread_id=st.session_state.thread.id )
                    for content_part in message.content:
                        if hasattr(content_part, 'text'):
                            with st.chat_message('assistant'):
                                st.write(content_part.text.value)
                    st.toast("MSG recibido y guardado")
                    st.session_state.messages_progress.append(messageid)
                


                    
        if st.session_state.retry_error < 3:
            time.sleep(4)
            st.rerun()
else:
    st.toast("No more status")
    
    
                            #run_steps = client.beta.threads.runs.steps.list(thread_id=st.session_state.thread.id,run_id=message.run_id  )
                            #st.write(run_steps.data)

