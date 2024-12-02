from flask import Flask, request, jsonify, render_template
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import time

app = Flask(__name__)

dotenv_path = os.path.join(os.path.dirname(__file__), 'chaves.env')
load_dotenv(dotenv_path=dotenv_path)

azureai_endpoint = os.getenv("AZURE_ENDPOINT")
API_KEY = os.getenv("AZURE_OPENAI_KEY")

def extract_text(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(" ", strip=True)
        return text
    else:
        return None

def translate_article(text, lang):
    headers = {
        "Content-Type": "application/json",
        "api-key": API_KEY,
    }
    
    payload = {
      "messages": [
        {
          "role": "system",
          "content": [{"type": "text", "text": "Você atua como tradutor de textos"}]
        },
        {
          "role": "user",
          "content": [{"type": "text", "text": f"traduza: {text} para o idioma {lang} e responda com a tradução no formato: markdown"}]
        }
      ],
      "temperature": 0.7,
      "top_p": 0.95,
      "max_tokens": 900
    }

    try:
        response = requests.post(azureai_endpoint, headers=headers, json=payload)
        response.raise_for_status()
    except requests.HTTPError as e:
        if e.response.status_code == 429:
            time.sleep(5)
            return translate_article(text, lang)
        else:
            return "Erro ao processar a tradução"

    return response.json()['choices'][0]['message']['content']

@app.route('/')
def index():
    return render_template('index.html') 

@app.route('/translate', methods=['POST'])
def translate():
    data = request.get_json()
    url = data['url']
    lang = data['lang']
    text = extract_text(url)
    if text:
        translated_text = translate_article(text, lang)
        return jsonify({'translatedText': translated_text})
    else:
        return jsonify({'translatedText': 'Erro ao extrair o texto da URL.'})

if __name__ == '__main__':
    app.run(debug=True)
