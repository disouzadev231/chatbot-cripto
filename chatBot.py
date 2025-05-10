from flask import Flask, request, jsonify
from google.cloud import dialogflowcx_v3beta1 as dialogflowcx
from google.api_core.client_options import ClientOptions
import os
import base64
import json
import asyncio
import aiohttp
from cachetools import TTLCache

app = Flask(__name__)

# ------------------- CONFIGURAÇÕES -------------------

key_base64 = os.environ.get("GOOGLE_CREDENTIALS_BASE64")
key_path = "keyfile.json"

if key_base64:
    with open(key_path, "wb") as f:
        f.write(base64.b64decode(key_base64))
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
else:
    raise Exception("Variável GOOGLE_CREDENTIALS_BASE64 não está definida.")

# Twilio
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"

# Reutilizar o cliente do Dialogflow
location = "us-central1"
api_endpoint = f"{location}-dialogflow.googleapis.com"
client_options = ClientOptions(api_endpoint=api_endpoint)
dialogflow_client = dialogflowcx.SessionsClient(client_options=client_options)

# Sessão HTTP global
http_session = aiohttp.ClientSession()

# Cache com tempo de vida de 60 segundos
cache = TTLCache(maxsize=100, ttl=60)

# ------------------- DIALOGFLOW CX -------------------

async def detect_intent_text_async(msg, session_id="sessao_123", project_id="careful-alloy-433019-u1",
                                   agent_id="8814b38a-995d-4bab-8290-5e51472f5650", language_code="pt-BR"):
    session_path = dialogflow_client.session_path(
        project=project_id,
        location=location,
        agent=agent_id,
        session=session_id
    )

    text_input = dialogflowcx.TextInput(text=msg)
    query_input = dialogflowcx.QueryInput(
        text=text_input,
        language_code=language_code
    )

    request = dialogflowcx.DetectIntentRequest(
        session=session_path,
        query_input=query_input
    )

    response = dialogflow_client.detect_intent(request=request)
    return response.query_result

# ------------------- FUNÇÕES AUXILIARES -------------------

async def get_bitcoin_price():
    if "bitcoin_price" in cache:
        return cache["bitcoin_price"]

    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=brl"
        async with http_session.get(url) as response:
            data = await response.json()
            price = data["bitcoin"]["brl"]
            result = f"\U0001F4B0 O preço atual do Bitcoin é R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            cache["bitcoin_price"] = result
            return result
    except Exception as e:
        print("⚠️ Erro ao buscar preço do Bitcoin:", e)
        return "❌ Erro ao buscar o preço do Bitcoin."

async def get_top_cryptos():
    if "top_cryptos" in cache:
        return cache["top_cryptos"]

    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "brl",
            "order": "market_cap_desc",
            "per_page": 3,
            "page": 1,
            "sparkline": False
        }
        async with http_session.get(url, params=params) as response:
            data = await response.json()

            reply_lines = ["\U0001F3C6 Top criptomoedas hoje:"]
            for i, coin in enumerate(data, start=1):
                name = coin["name"]
                symbol = coin["symbol"].upper()
                price = f"R$ {coin['current_price']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                reply_lines.append(f"{i}⃣ {name} ({symbol}) - {price}")

            result = "\n".join(reply_lines)
            cache["top_cryptos"] = result
            return result
    except Exception as e:
        print("⚠️ Erro ao buscar top criptos:", e)
        return "❌ Não foi possível obter as principais criptomoedas no momento."

async def send_message(to, message):
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    auth = aiohttp.BasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    payload = {
        "To": to,
        "From": TWILIO_WHATSAPP_NUMBER,
        "Body": message
    }

    async with http_session.post(url, data=payload, auth=auth) as response:
        print("\U0001F4E4 Enviado para Twilio:", response.status, await response.text())

# Função para explicar o que é uma criptomoeda
def explain_crypto():
    return "Criptomoedas são moedas digitais descentralizadas baseadas em tecnologia blockchain."

# Função para mensagem de boas-vindas
def welcome_message():
    return "Bem-vindo ao Chatbot Cripto! Como posso ajudar você hoje?"

# ------------------- WEBHOOK -------------------------

@app.route("/webhook", methods=["POST"])
async def webhook():
    try:
        if request.form and request.form.get("Body") and request.form.get("From"):
            data = request.form
            print("📩 Mensagem recebida (WhatsApp):", json.dumps(data.to_dict(), indent=2))

            msg = data.get("Body")
            sender = data.get("From")

            try:
                result = await detect_intent_text_async(msg)
                tag = result.fulfillment_info.tag.strip()

                print(f"🔖 Tag recebida: '{tag}'")

                if tag == "ConsultarPrecoBitcoin":
                    reply = await get_bitcoin_price()
                elif tag == "ConsultarTopCriptos":
                    reply = await get_top_cryptos()
                elif tag == "ExplicarCriptomoeda":
                    reply = explain_crypto()
                elif tag == "BoasVindas":
                    reply = welcome_message()
                else:
                    reply = "Desculpe, não entendi sua pergunta."

                await send_message(sender, reply)

            except Exception as e:
                print("❌ Erro ao processar mensagem:", e)

            return jsonify({"status": "accepted"}), 200

        else:
            data = request.get_json()
            print("📩 Requisição recebida do Dialogflow:", json.dumps(data, indent=2))

            tag = data.get("fulfillmentInfo", {}).get("tag", "").strip()
            print(f"🔖 Tag recebida (direto): '{tag}'")

            reply = "❓ Desculpe, não entendi."

            if tag == "ConsultarPrecoBitcoin":
                reply = await get_bitcoin_price()
            elif tag == "ConsultarTopCriptos":
                reply = await get_top_cryptos()
            elif tag == "ExplicarCriptomoeda":
                reply = explain_crypto()
            elif tag == "BoasVindas":
                reply = welcome_message()

            return jsonify({
                "fulfillment_response": {
                    "messages": [{"text": {"text": [reply]}}]
                }
            })

    except Exception as e:
        print("❌ Erro:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

# ------------------- RAIZ ----------------------------

@app.route("/", methods=["GET"])
def home():
    return "Chatbot Cripto ativo!", 200

# ------------------- MAIN ----------------------------

if __name__ == "__main__":
    app.run(debug=False)
