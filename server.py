# server.py

from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
from flask_cors import CORS
from flask_session import Session
from oauthlib.oauth2 import WebApplicationClient
import requests
import os
import json

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Secret key for session
app.secret_key = os.environ.get("SECRET_KEY", "supersecret")

# Session config
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# OAuth2 client setup
GOOGLE_CLIENT_ID = json.load(open("client_secrets.json"))["web"]["client_id"]
GOOGLE_CLIENT_SECRET = json.load(open("client_secrets.json"))["web"]["client_secret"]
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Load db
if os.path.exists("db.json"):
    with open("db.json", "r") as f:
        chats = json.load(f)
else:
    chats = {}

# Helpers
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

def save_db():
    with open("db.json", "w") as f:
        json.dump(chats, f)

@app.route("/")
def index():
    return send_from_directory('.', 'index.html')

@app.route("/login")
def login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route("/login/callback")
def callback():
    code = request.args.get("code")
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    client.parse_request_body_response(json.dumps(token_response.json()))
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
        
        session["user"] = users_name
        session["email"] = users_email

    return redirect(url_for("index"))

@app.route("/profile")
def profile():
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401
    return jsonify({"user": session["user"], "email": session["email"]})

@app.route("/chat", methods=["POST"])
def chat():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_input = request.json.get("message")
    chat_id = request.json.get("chat_id")

    if not chat_id:
        chat_id = str(len(chats) + 1)
        chats[chat_id] = []

    # Here normally you would connect to GPT API
    response = f"Echo: {user_input}"  # Dummy for now

    chats[chat_id].append({"user": user_input, "bot": response})
    save_db()
    
    return jsonify({"reply": response, "chat_id": chat_id})

@app.route("/generate_image", methods=["POST"])
def generate_image():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    description = request.json.get("prompt")

    # Normally call DALL-E or other model here
    fake_image_url = "https://via.placeholder.com/300?text=" + description.replace(" ", "+")

    return jsonify({"image_url": fake_image_url})

@app.route("/chats")
def list_chats():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    titles = {}
    for cid, messages in chats.items():
        if messages:
            titles[cid] = messages[0]['user']
    return jsonify(titles)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860, debug=True)
