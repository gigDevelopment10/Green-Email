import os
import pathlib

import requests
from flask import Flask, session, abort, redirect, request, render_template
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import email
from email.mime.text import MIMEText
import base64

app = Flask("Google Login App")
app.secret_key = "CodeSpecialist.com"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "482929997543-k53paie07e7v47oqngo1j100obpfr29i.apps.googleusercontent.com"
client_secrets_file = os.path.join(
    pathlib.Path(__file__).parent, "credentials.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email", "openid", 'https://www.googleapis.com/auth/gmail.modify'],
    redirect_uri="http://127.0.0.1:5000/callback"
)


def login_is_required(function):
    def wrapper(*args, **kwargs):

        if "google_id" not in session:
            return redirect("/")  # Authorization required
        else:
            try:
                Credentials = flow.credentials
                return function()
            except:
                return redirect("/")

    return wrapper


@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials

    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(
        session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    return redirect("/protected_area")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/")
def index():
    return "Hello World <a href='/login'><button>Login</button></a>"

def get_all_mails(service, label):
    results = service.users().messages().list(userId='me', labelIds=[label]).execute()
    messages = results.get('messages', [])
    while 'nextPageToken' in results:
        page_token = results['nextPageToken']
        results = service.users().messages().list(userId='me', labelIds=[label], pageToken=page_token).execute()
        messages.extend(results['messages'])
    return messages


def get_message(service, user_id, msg_id):
    """
    Search the inbox for specific message by ID and return it back as a 
    clean string. String may contain Python escape characters for newline
    and return line. 
    
    PARAMS
        service: the google api service object already instantiated
        user_id: user id for google api service ('me' works here if
        already authenticated)
        msg_id: the unique id of the email you need
    RETURNS
        A string of encoded text containing the message body
    """
    try:
        # grab the message instance
        message = service.users().messages().get(
            userId=user_id, id=msg_id, format='raw').execute()
        
        """
        message_format = {
    "id": string,
    "threadId": string,
    "labelIds": [
        string
    ],
    "snippet": string,
    "historyId": string,
    "internalDate": string,
    "payload": {
        object (MessagePart)
    },
    "sizeEstimate": integer,
    "raw": string
    }

    payload = {
    "partId": string,
    "mimeType": string,
    "filename": string,
    "headers": [
        {
        object (Header)
        }
    ],
    "body": {
        object (MessagePartBody)
    },
    "parts": [
        {
        object (MessagePart)
        }
    ]
    }

    headers = {
    "name": string,
    "value": string
    }

    body = {
    "size": integer,
    "data": string,
    "attachmentId": string
    }

    
        """

        # decode the raw string, ASCII works pretty well here
        msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))

        # grab the string from the byte object
        mime_msg = email.message_from_bytes(msg_str)

        # check if the content is multipart (it usually is)
        content_type = mime_msg.get_content_maintype()
        if content_type == 'multipart':
            # there will usually be 2 parts the first will be the body in text
            # the second will be the text in html
            parts = mime_msg.get_payload()

            # return the encoded text
            final_content = parts[0].get_payload()
            return final_content

        elif content_type == 'text':
            return mime_msg.get_payload()

        else:
            return ""
            print("\nMessage is not text or multipart, returned an empty string")
    # unsure why the usual exception doesn't work in this case, but
    # having a standard Exception seems to do the trick
    except Exception:
        print("An error occured")



@app.route("/protected_area")
@login_is_required
def protected_area():
    credentials = flow.credentials
    service = build('gmail', 'v1', credentials=credentials)
    labels = ['UNREAD']
    # labels = ['CHAT','TRASH','SPAM','CATEGORY_FORUMS','CATEGORY_UPDATES','CATEGORY_PROMOTIONS','CATEGORY_SOCIAL','UNREAD']
    
    for label in labels:
        # get all the mails with label = label
        messages = get_all_mails(service, label)
        for message in messages:
            # get the message body
            msg = get_message(service, 'me', message['id'])
            # print the message body
            print(msg)

    return f"Hello Om ! <br/> <a href='/logout'><button>Logout</button></a>"

# make a route for privacy policy


@app.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy_policy.html")


if __name__ == "__main__":
    app.run(debug=True)
