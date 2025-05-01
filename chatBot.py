from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import requests

app = Flask(__name__)

# Função para lidar com a consulta de preço do Bitcoin
def handle_btc_price():
    r = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=brl')
    data = r.json()
    price = data['bitcoin']['brl']
    return f"💰 O preço atual do Bitcoin é R$ {price:,.2f}"

# Função para lidar com as 5 criptos mais populares
def handle_top_cryptos():
    r = requests.get('https://api.coingecko.com/api/v3/coins/markets', params={
        'vs_currency': 'brl',
        'order': 'market_cap_desc',
        'per_page': 5,
        'page': 1
    })
    data = r.json()
    top = "\n".join([f"{i+1}. {coin['name']} (R$ {coin['current_price']:,.2f})" for i, coin in enumerate(data)])
    return f"📊 Top 5 criptomoedas hoje:\n{top}"

# Função para lidar com a explicação de criptomoedas
def handle_explain_crypto(req):
    user_text = req.lower()
    explicacoes = {
        "bitcoin": "Bitcoin é a primeira criptomoeda, criada em 2009. Funciona como dinheiro digital descentralizado.",
        "ethereum": "Ethereum é uma plataforma que permite contratos inteligentes e aplicativos descentralizados.",
        "solana": "Solana é uma blockchain de alta performance voltada para aplicativos descentralizados.",
        "dogecoin": "Dogecoin começou como uma piada, mas ganhou popularidade como moeda digital de gorjetas.",
        "cardano": "Cardano é uma blockchain focada em sustentabilidade e segurança, fundada por um dos cofundadores do Ethereum."
    }

    for moeda, explicacao in explicacoes.items():
        if moeda in user_text:
            return explicacao

    return "❓ Ainda não tenho informações sobre essa criptomoeda."

# Função de resposta padrão
def default_response():
    return "🤖 Desculpe, não entendi. Pode repetir?"

# Rota do webhook para comunicação com o Dialogflow
@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json()  # Dados recebidos do Dialogflow
    intent = req.get('queryResult', {}).get('intent', {}).get('displayName', '')

    # Checa qual intenção foi ativada e chama a função correspondente
    if intent == "ConsultarPrecoBitcoin":
        response = handle_btc_price()
    elif intent == "ConsultarTopCriptos":
        response = handle_top_cryptos()
    elif intent == "ExplicarCriptomoeda":
        response = handle_explain_crypto(req)
    else:
        response = default_response()

    # Envia a resposta para o Dialogflow em formato JSON
    return jsonify({
        "fulfillmentText": response
    })

# Rota para receber e responder via WhatsApp (Twilio)
@app.route('/whatsapp', methods=['POST'])
def whatsapp():
    incoming_msg = request.values.get('Body', '').lower()
    response = MessagingResponse()

    if 'preço bitcoin' in incoming_msg:
        response.message(handle_btc_price())
    elif 'top 5' in incoming_msg:
        response.message(handle_top_cryptos())
    elif 'explicar' in incoming_msg:
        response.message(handle_explain_crypto(incoming_msg))
    else:
        response.message(default_response())

    return str(response)

# Inicia o servidor Flask
if __name__ == "__main__":
    app.run()
