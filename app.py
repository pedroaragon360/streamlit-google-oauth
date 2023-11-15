import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import requests
import streamlit.components.v1 as components

# Define the OAuth2 scopes
SCOPES = ['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']

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

# JavaScript to listen for the auth code
def listen_for_auth_code():
    js = """
    <script>
    window.addEventListener('message', (event) => {
        if (event.data.type === 'authCode') {
            const authCode = event.data.code;
            // Send auth code to Streamlit's server
            // ... [handle the auth code in Streamlit] ...
        }
    }, false);
    </script>
    """
    components.html(js, height=0)

# Streamlit app layout
def main():
    flow = init_flow()
    listen_for_auth_code()

    if 'credentials' not in st.session_state:
        # Display login screen
        st.title("Login with Google")
        auth_url, _ = flow.authorization_url(prompt='consent')
        st.markdown(f'<a href="{auth_url}" target="_blank">Login</a>', unsafe_allow_html=True)

    if 'credentials' in st.session_state:
        # User is authenticated, show the content screen
        st.title("Welcome to the App")
        credentials = Credentials.from_authorized_user_info(st.session_state['credentials'])

        # Make a request to Google's user info endpoint
        userinfo_response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {credentials.token}'}
        )

        user_info = userinfo_response.json()
        st.write(f"User info: {user_info}")

# Run the app
if __name__ == "__main__":
    main()
