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

# Function to capture URL parameters with JavaScript
def get_url_params():
    js = """
    window.onload = () => {
        const urlParams = new URLSearchParams(window.location.search);
        const params = Object.fromEntries(urlParams.entries());
        if (Object.keys(params).length > 0) {
            window.parent.postMessage({type: 'urlParams', data: params}, '*');
        }
    }
    """
    components.html(f"<script>{js}</script>", height=0)

# Streamlit app layout
def main():
    get_url_params()
    flow = init_flow()

    # Check for URL parameters in session state
    if 'urlParams' in st.session_state:
        params = st.session_state.urlParams
        if 'code' in params and 'state' in params:
            # Complete the authentication process
            flow.fetch_token(code=params['code'])
            credentials = flow.credentials
            st.session_state['credentials'] = credentials.to_json()
            del st.session_state['urlParams']

    if 'credentials' not in st.session_state:
        # Display login screen
        st.title("Login with Google")
        auth_url, _ = flow.authorization_url(prompt='consent')
        st.markdown(f'[Login]({auth_url})', unsafe_allow_html=True)
    else:
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
