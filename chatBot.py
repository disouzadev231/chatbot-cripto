from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os

app = Flask(__name__)

# ⚙️ Defina essas variáveis com seus dados reais do Dialogflow CX
PROJECT_ID = "SEU_PROJECT_ID"
LOCATION = "global"  # ou "us-central1"
AGENT_ID = "SEU_AGENT_ID"
SESSION_ID = "qualquer-session-id-unico"
LANGUAGE_CODE = "pt-br"
ACCESS_TOKEN = "SEU_TOKEN_DE_AUTORIZACAO_DIALOGFLOW"

def detect_intent_text(text, session_id=SESSION_ID):
    url = f"https://dialogflow.googleapis.com/v3/projects/{PROJECT_ID}/locations/{LOCATION}/agents/{AGENT_ID}/sessions/{session_id}:detectIntent"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
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

    # Chama o Dialogflow CX
    df_response = detect_intent_text(incoming_msg)

    try:
        msg = df_response["fulfillmentResponse"]["messages"][0]["text"]["text"][0]
    except Exception as e:
        msg = "⚠️ Houve um erro ao processar sua mensagem."

    response.message(msg)
    return str(response)

if __name__ == "__main__":
    app.run()
