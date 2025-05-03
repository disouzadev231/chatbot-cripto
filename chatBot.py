from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import json
import os
from google.oauth2 import service_account
import google.auth.transport.requests

app = Flask(__name__)

# Configurações do Dialogflow CX
PROJECT_ID = "careful-alloy-433019-u1"
LOCATION = "global"
AGENT_ID = "3e7c7703-9ad7-4943-ab42-954363eda079"
SESSION_ID = "sessao_381485_usuarioA"
LANGUAGE_CODE = "pt-br"

# Carrega as credenciais do JSON a partir da variável de ambiente
service_account_info = json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
credentials = service_account.Credentials.from_service_account_info(
    service_account_info, scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

def generate_access_token():
    request_auth = google.auth.transport.requests.Request()
    credentials.refresh(request_auth)
    return credentials.token

def detect_intent_text(text, session_id=SESSION_ID):
    access_token = generate_access_token()
    url = f"https://dialogflow.googleapis.com/v3/projects/{PROJECT_ID}/locations/{LOCATION}/agents/{AGENT_ID}/sessions/{session_id}:detectIntent"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "queryInput": {
            "text": {
                "text": text
            },
            "languageCode": LANGUAGE_CODE
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.json()

@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_msg = request.values.get('Body', '').strip()
    response = MessagingResponse()

    if not incoming_msg:
        response.message("❗ Não entendi sua mensagem.")
        return str(response)

    try:
        df_response = detect_intent_text(incoming_msg)
        messages = df_response.get("fulfillmentResponse", {}).get("messages", [])
    except Exception as e:
        print(f"Erro: {e}")
        msg = "⚠️ Houve um erro ao processar sua mensagem."

    response.message(msg)
    return str(response)

if __name__ == "__main__":
    app.run(debug=True)
