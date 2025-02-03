import os, json
from utils import start_download
from flask import Flask, render_template, session, redirect, url_for, request, jsonify
from fief_client import Fief
from fief_client.integrations.flask import (
    FiefAuth,
    FiefAuthForbidden,
    FiefAuthUnauthorized,
    get_authorization_scheme_token,
)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "a-very-secret-key")

# --------------------------------------------------------------------------------
# Fief Configuration from environment variables
# (Update these in docker-compose.yml or your system environment)
# --------------------------------------------------------------------------------
FIEF_BASE_URL = os.getenv("FIEF_BASE_URL", "https://example.fief.dev")
FIEF_CLIENT_ID = os.getenv("FIEF_CLIENT_ID", "YOUR_FIEF_CLIENT_ID")
FIEF_CLIENT_SECRET = os.getenv("FIEF_CLIENT_SECRET", "YOUR_FIEF_CLIENT_SECRET")

fief = Fief(
    base_url=FIEF_BASE_URL,
    client_id=FIEF_CLIENT_ID,
    client_secret=FIEF_CLIENT_SECRET,
    # Depending on your Fief setup, you may also specify scopes, audiences, etc.
)


with open('favicons.json', 'r', encoding='utf-8') as f:
    favicons = json.load(f)

# --------------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------------

@app.route("/")
def index():
    """
    Main page (unprotected). Shows the Bootstrap 5 template.
    If user is logged in, we can display extra info or simply show a "logout" link.
    """

    return render_template("index.html", favicons=favicons)

@app.route('/download', methods=['POST'])
def download():
    # Load JSON Payload
    data = request.json
    url = data['url']
    try:
        id = start_download(url)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"id": id}), 200

@app.route('/stream/<id>')
def stream(id):
    status = "Pending"
    link = "https://dl.getthis.stream/"+id
    progress = 75
    return render_template('stream.html', favicons=favicons, status=status, link=link, progress=progress)

@app.route("/login")
def login():
    """
    Redirects to Fief's auth page. Once user logs in, Fief will redirect
    back to /callback with a 'code'.
    """
    redirect_uri = url_for("callback", _external=True)
    auth_url = fief.auth_url(redirect_uri)
    return redirect(auth_url)

@app.route("/callback")
def callback():
    """
    Exchange the authorization code for tokens, store them in session,
    then redirect back to the main page (or a protected route).
    """
    code = request.args.get("code")
    if not code:
        return "Missing 'code' parameter", 400

    redirect_uri = url_for("callback", _external=True)
    token_response = fief.auth_callback(code, redirect_uri)

    # Store tokens in session
    session["access_token"] = token_response["access_token"]
    # If you need refresh tokens or ID tokens, store them as well
    # session["refresh_token"] = token_response["refresh_token"]
    # session["id_token"] = token_response["id_token"]

    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    """
    Clears session tokens. You can also optionally revoke tokens
    or redirect to Fief's logout endpoint.
    """
    session.pop("access_token", None)
    # For a full sign-out, you can also redirect to Fief's end_session_endpoint:
    # return redirect(f"{FIEF_BASE_URL}/logout?redirect_uri={url_for('index', _external=True)}")
    return redirect(url_for("index"))

# --------------------------------------------------------------------------------
# Entry Point
# --------------------------------------------------------------------------------

if __name__ == "__main__":
    # For local dev testing; in Docker, Gunicorn will be used
    app.run(host="0.0.0.0", port=5000, debug=True)
