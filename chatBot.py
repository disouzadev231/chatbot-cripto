from flask import Flask, request, jsonify
from google.cloud import dialogflow_v2 as dialogflow
from google.cloud import dialogflowcx_v3beta1 as dialogflowcx
from google.api_core.client_options import ClientOptions
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

# ------------------- DIALOGFLOW CX -------------------

def detect_intent_text(
    msg,
    session_id="sessao_123",
    project_id="careful-alloy-433019",
    agent_id="8814b38a-995d-4bab-8290-5e51472f5650",
    location="us-central1",
    language_code="pt-BR"
):
    location = location.replace(" ", "").strip()
    print(f"🔍 Location recebido: '{location}'")

    # Define o endpoint regional para evitar erro 400
    api_endpoint = f"{location}-dialogflow.googleapis.com"
    client_options = ClientOptions(api_endpoint=api_endpoint)
    client = dialogflowcx.SessionsClient(client_options=client_options)

    # Define o caminho da sessão
    session_path = client.session_path(
        project=project_id,
        location=location,
        agent=agent_id,
        session=session_id
    )

    # Monta a requisição
    text_input = dialogflowcx.TextInput(text=msg)
    query_input = dialogflowcx.QueryInput(
        text=text_input,
        language_code=language_code
    )

    request = dialogflowcx.DetectIntentRequest(
        session=session_path,
        query_input=query_input
    )

    # Executa e retorna a resposta
    response = client.detect_intent(request=request)
    return response.query_result.response_messages

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

        df_messages = detect_intent_text(msg)
        reply = "Desculpe, não entendi sua pergunta."

        for m in df_messages:
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
