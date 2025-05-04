from flask import Flask, request, jsonify
from google.cloud import dialogflow_v2 as dialogflow
import os
import base64
import requests
import json

app = Flask(__name__)

# ------------------- CONFIGURAÇÕES -------------------

# Decodifica a chave do Dialogflow de uma variável de ambiente base64
key_base64 = os.environ.get("GOOGLE_CREDENTIALS_BASE64")
key_path = "keyfile.json"

if key_base64:
    with open(key_path, "wb") as f:
        f.write(base64.b64decode(key_base64))
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
else:
    raise Exception("Variável de ambiente GOOGLE_CREDENTIALS_BASE64 não está definida.")

# Dados da Twilio
TWILIO_ACCOUNT_SID = "SEU_ACCOUNT_SID"
TWILIO_AUTH_TOKEN = "SEU_AUTH_TOKEN"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"

# ------------------- DIALOGFLOW ----------------------

def detect_intent_text(msg, session_id="sessao_123", language_code="pt-BR"):
    client = dialogflow.SessionsClient()
    session = client.session_path("careful-alloy-433019-u1", session_id)

    text_input = dialogflow.TextInput(text=msg, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)

    response = client.detect_intent(request={"session": session, "query_input": query_input})
    return response

# ------------------- ENVIO TWILIO --------------------

def send_message(to, message):
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    payload = {
        "To": to,
        "From": TWILIO_WHATSAPP_NUMBER,
        "Body": message
    }

    response = requests.post(url, data=payload, auth=auth)
    print("📤 Enviado para Twilio:", response.status_code, response.text)

# ------------------- WEBHOOK -------------------------

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.form
    print("📩 Mensagem recebida:", json.dumps(data.to_dict(), indent=2))

    try:
        msg = data.get("Body")
        sender = data.get("From")

        df_response = detect_intent_text(msg)
        reply = "Desculpe, não entendi sua pergunta."

        for m in df_response.query_result.response_messages:
            if m.text and m.text.text:
                reply = m.text.text[0]
                break

        send_message(sender, reply)
        return jsonify({"status": "success"}), 200

    except Exception as e:
        print("❌ Erro:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

# ------------------- RAIZ ----------------------------

@app.route("/", methods=["GET"])
def home():
    return "Chatbot Cripto ativo!", 200

# ------------------- MAIN ----------------------------

if __name__ == "__main__":
    app.run(debug=True)
