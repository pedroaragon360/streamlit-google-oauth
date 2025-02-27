import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import requests

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

# Function to perform authentication
def authenticate_user(flow):
    authorization_url, state = flow.authorization_url()
    st.session_state['state'] = state
    return authorization_url

# Function to handle callback from Google OAuth
def callback(flow):
    flow.fetch_token(authorization_response=st.session_state['auth_url'])
    credentials = flow.credentials
    return credentials

# Streamlit app layout
def main():
    flow = init_flow()

    # Check if the user is already authenticated
    if 'credentials' not in st.session_state:
        # Display login screen
        st.title("Login with Google")
        auth_url = authenticate_user(flow)
        st.markdown(f'[Login]({auth_url})', unsafe_allow_html=True)

        if 'auth_url' in st.session_state:
            credentials = callback(flow)
            st.session_state['credentials'] = credentials.to_json()

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
