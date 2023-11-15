import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import requests
import json  # Import the json module

# Define the OAuth2 scopes
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'  # Include the 'openid' scope
]

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
            st.error("An error occurred during authentication. Please try logging in again.")
            st.markdown(f'[Login]({flow.authorization_url(prompt="consent")[0]})', unsafe_allow_html=True)
            return
            
    if 'credentials' not in st.session_state:
        # Display login screen
        st.title("Login with Google")
        auth_url, _ = flow.authorization_url(prompt='consent')
        st.markdown(f'<a href="{auth_url}">Login</a>', unsafe_allow_html=True)

    else:
        # User is authenticated, show the content screen
        st.title("Welcome to the App")
        # Convert JSON string back to dictionary
        credentials_dict = json.loads(st.session_state['credentials'])
        credentials = Credentials.from_authorized_user_info(credentials_dict)
        
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
