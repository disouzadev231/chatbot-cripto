from flask import Flask, request, jsonify
from google.cloud import dialogflow_v2 as dialogflow
from google.cloud import dialogflowcx_v3beta1 as dialogflowcx
from google.api_core.client_options import ClientOptions
from google.auth import default
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

# Verifica a conta de serviço ativa
creds, _ = default()
print(f"🔐 Conta de serviço ativa: {creds.service_account_email}")

# Dados da Twilio
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")

TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"

# ------------------- DIALOGFLOW CX -------------------

def detect_intent_text(
    msg,
    session_id="sessao_123",
    project_id="careful-alloy-433019-u1",
    agent_id="8814b38a-995d-4bab-8290-5e51472f5650",
    location="us-central1",
    language_code="pt-BR"
):
    location = location.replace(" ", "").strip()
    print(f"🔍 Location recebido: '{location}'")

    # Define o endpoint regional
    api_endpoint = f"{location}-dialogflow.googleapis.com"
    client_options = ClientOptions(api_endpoint=api_endpoint)
    client = dialogflowcx.SessionsClient(client_options=client_options)

    # Caminho da sessão
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

    # Envia a requisição
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

# ------------------- FUNÇÕES AUXILIARES -------------------

def get_bitcoin_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=brl"
        response = requests.get(url)
        data = response.json()
        price = data["bitcoin"]["brl"]
        return f"💰 O preço atual do Bitcoin é R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception as e:
        print("⚠️ Erro ao buscar preço do Bitcoin:", e)
        return "❌ Erro ao buscar o preço do Bitcoin."

def get_top_cryptos():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "brl",
            "order": "market_cap_desc",
            "per_page": 3,
            "page": 1,
            "sparkline": False
        }
        response = requests.get(url, params=params)
        data = response.json()

        reply_lines = ["🏆 Top criptomoedas hoje:"]
        for i, coin in enumerate(data, start=1):
            name = coin["name"]
            symbol = coin["symbol"].upper()
            price = f"R$ {coin['current_price']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            reply_lines.append(f"{i}️⃣ {name} ({symbol}) - {price}")

        return "\n".join(reply_lines)

    except Exception as e:
        print("⚠️ Erro ao buscar top criptos:", e)
        return "❌ Não foi possível obter as principais criptomoedas no momento."


def explain_crypto():
    return (
        "🔍 Criptomoedas são moedas digitais descentralizadas que utilizam a tecnologia blockchain "
        "para garantir segurança e transparência nas transações."
    )

def welcome_message():
    return (
        "👋 Olá! Bem-vindo ao ChatCriptoMVP.\n"
        "Você pode me perguntar sobre o preço do Bitcoin, criptos em destaque ou o que é blockchain!"
    )

# ------------------- WEBHOOK -------------------

@app.route("/webhook", methods=["POST"])
def webhook():
    # Verifica se é requisição do WhatsApp ou Dialogflow
    if request.form and request.form.get("From"):
        # WhatsApp / Twilio
        data = request.form
        print("📩 Mensagem recebida:", json.dumps(data.to_dict(), indent=2))

        try:
            msg = data.get("Body")
            sender = data.get("From")

            df_messages = detect_intent_text(msg)
            reply = "Desculpe, não entendi sua pergunta."

            tag = None

            for m in df_messages:
                if m.payload:
                    tag = m.payload.get("fields", {}).get("tag", {}).get("stringValue", "")
                if m.text and m.text.text:
                    reply = m.text.text[0]

            # Verifica a tag para resposta dinâmica
            if tag == "ConsultarPrecoBitcoin":
                reply = get_bitcoin_price()
            elif tag == "ConsultarTopCriptos":
                reply = get_top_cryptos()
            elif tag == "ExplicarCriptomoeda":
                reply = explain_crypto()
            elif tag == "BoasVindas":
                reply = welcome_message()

            send_message(sender, reply)
            return jsonify({"status": "success"}), 200

        except Exception as e:
            print("❌ Erro:", e)
            return jsonify({"status": "error", "message": str(e)}), 500

    else:
        # Fulfillment direto do Dialogflow (sem dados de WhatsApp)
        print("⚠️ Ignorado: Requisição sem dados do WhatsApp.")
        return jsonify({"status": "ignored", "message": "Requisição sem dados do WhatsApp."}), 200


# ------------------- RAIZ ----------------------------

@app.route("/", methods=["GET"])
def home():
    return "Chatbot Cripto ativo!", 200

# ------------------- MAIN ----------------------------

if __name__ == "__main__":
    app.run(debug=True)
