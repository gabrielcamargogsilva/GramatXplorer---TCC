# utils/groq_firebase.py

import requests
import os
import json
import random
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def chamar_groq(mensagem_user, mensagem_sistema=""):
    """Função para chamar a API Groq."""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": mensagem_sistema},
            {"role": "user", "content": mensagem_user}
        ],
        "temperature": 0.7,
    }
    try:
        response = requests.post(GROQ_URL, headers=headers, json=body)
        response.raise_for_status()
        resposta = response.json()
        return resposta['choices'][0]['message']['content'].strip(), 200
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao chamar Groq API: {e}")
        return None, 500

def obter_perguntas_reservas(db, nivel: str, tema: str, limite: int):
    """
    Busca perguntas de reserva no Firebase (coleção 'perguntas_reservas')
    filtrando por nível e tema como plano de contingência.
    """
    if not db:
        print("❌ Firebase DB não está conectado. Não foi possível buscar reservas.")
        return []
        
    try:
        perguntas_ref = db.collection('perguntas_reserva')
        # Filtra por NÍVEL e TEMA
        query = perguntas_ref.where('nivel', '==', nivel).where('tema', '==', tema).stream()
        
        perguntas_filtradas = []
        for doc in query:
            pergunta_data = doc.to_dict()
            # Tenta converter o ID (nome do documento) para int, senão mantém como string
            try:
                pergunta_data['id'] = int(doc.id)
            except ValueError:
                pergunta_data['id'] = doc.id
                
            perguntas_filtradas.append(pergunta_data)

        # Seleciona aleatoriamente se houver mais do que o limite solicitado
        if len(perguntas_filtradas) > limite:
            perguntas_selecionadas = random.sample(perguntas_filtradas, limite)
        else:
            perguntas_selecionadas = perguntas_filtradas

        print(f"✅ Perguntas de reserva obtidas do Firebase: {len(perguntas_selecionadas)} perguntas.")
        return perguntas_selecionadas

    except Exception as e:
        print(f"❌ Erro ao buscar perguntas de reserva no Firebase: {e}")
        return []