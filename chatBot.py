from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json()
    intent = req.get('fulfillmentInfo', {}).get('tag', '')

    if intent == "ConsultarPrecoBitcoin":
        response = handle_btc_price()
    elif intent == "ConsultarTopCriptos":
        response = handle_top_cryptos()
    elif intent == "ExplicarCriptomoeda":
        response = handle_explain_crypto(req)
    else:
        response = default_response()

    return jsonify(response)

def handle_btc_price():
    r = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=brl')
    price = r.json()['bitcoin']['brl']
    return make_response(f"💰 O preço atual do Bitcoin é R$ {price:,.2f}")

def handle_top_cryptos():
    r = requests.get('https://api.coingecko.com/api/v3/coins/markets', params={
        'vs_currency': 'brl',
        'order': 'market_cap_desc',
        'per_page': 5,
        'page': 1
    })
    data = r.json()
    top = "\n".join([f"{i+1}. {coin['name']} (R$ {coin['current_price']:,.2f})" for i, coin in enumerate(data)])
    return make_response(f"📊 Top 5 criptomoedas hoje:\n{top}")

def handle_explain_crypto(req):
    user_text = req.get('text', '').lower()
    explicacoes = {
        "bitcoin": "Bitcoin é a primeira criptomoeda...",
        "ethereum": "Ethereum é uma plataforma...",
        "solana": "Solana é uma blockchain...",
        "dogecoin": "Dogecoin começou como uma piada...",
        "cardano": "Cardano é uma blockchain segura..."
    }
    for moeda, explicacao in explicacoes.items():
        if moeda in user_text:
            return make_response(explicacao)
    return make_response("❓ Ainda não tenho informações sobre essa criptomoeda.")

def default_response():
    return make_response("🤖 Desculpe, não entendi. Pode repetir?")

def make_response(text):
    return {
        "fulfillment_response": {
            "messages": [
                {
                    "text": {
                        "text": [text]
                    }
                }
            ]
        }
    }

if __name__ == "__main__":
    app.run(port=5000)
