# api/vialactea.py

from flask import Blueprint, request, jsonify, current_app
import json
from config_data import temas_disponiveis, contexto_dificuldade
from utils.groq_firebase import chamar_groq, obter_perguntas_reservas

vialactea_bp = Blueprint('vialactea', __name__)

# ----------------------------------------------------------------------
# 🔹 Rota para gerar perguntas (COM LÓGICA DE CONTINGÊNCIA)
# ----------------------------------------------------------------------
@vialactea_bp.route('/perguntas', methods=['GET'])
def gerar_perguntas():
    db_client = current_app.config.get('DB')

    nivel = request.args.get('nivel', 'medio').lower()
    tema_solicitado = request.args.get('tema', '').lower()
    num_perguntas = 12

    if nivel not in ['facil', 'medio', 'dificil']:
        return jsonify({"erro": "Nível inválido. Use: fácil, médio ou difícil."}), 400
        
    if not tema_solicitado:
        return jsonify({"erro": "O parâmetro 'tema' é obrigatório para gerar as perguntas."}), 400
        
    tema_para_prompt = temas_disponiveis.get(tema_solicitado)
    if not tema_para_prompt:
        return jsonify({"erro": "Tema inválido. Temas disponíveis: " + ', '.join(temas_disponiveis.keys())}), 400

    prompt = (
        f"Você é um professor experiente de Língua Portuguesa voltado para o ensino médio. "
        f"Crie {num_perguntas} questões de gramática contextualizadas, de múltipla escolha, com 4 alternativas (A, B, C, D), sendo apenas uma correta. Tem que ser exatamente {num_perguntas} perguntas geradas, não pode ser mais e nem menos."
        f"A dificuldade deve ser de nível '{nivel}'. {contexto_dificuldade[nivel]} "
        f"As questões devem abordar conteúdos como: {tema_para_prompt} "
        "Para cada questão, forneça o subtema específico e uma explicação concisa e direta, focada apenas na justificativa da resposta. "
        "Retorne a resposta em um formato JSON, sendo um array de objetos. "
        "Não inclua qualquer texto antes ou depois do JSON. "
        # ... (Estrutura do JSON no prompt, como no código original) ...
        # (O restante do prompt foi omitido aqui para brevidade, mas deve ser o original)
    )
    
    # 1. Tenta chamar a IA (Groq)
    resposta_groq, status = chamar_groq(prompt, "Você é um professor de português criando um quiz de múltipla escolha. Retorne as questões em JSON.")
    
    # 2. Lógica de Contingência (Falha na API)
    if not resposta_groq or status != 200:
        print(f"🚨 Falha na Groq API (Status: {status}). Ativando plano de contingência do Firebase...")
        
        perguntas_reservas = obter_perguntas_reservas(db_client,nivel, tema_solicitado, num_perguntas)

        if perguntas_reservas:
            return jsonify(perguntas_reservas), 200
        else:
            return jsonify({"erro": "Erro na chamada da Groq API e o banco de perguntas de reserva está indisponível ou vazio para o tema/nível solicitado."}), 503 

    # 3. Processamento normal da resposta da IA
    try:
        # Lógica de limpeza e validação de JSON (como no seu código original)
        resposta_limpa = resposta_groq.strip().lstrip('`json\n').lstrip('`python\n').rstrip('`')
        perguntas = json.loads(resposta_limpa)
        
        if not isinstance(perguntas, list):
            raise ValueError(f"A resposta da IA não é uma lista.")
        # ... (Restante da validação e atribuição de ID) ...

        for i, pergunta in enumerate(perguntas):
            pergunta['id'] = i + 1 
            
        return jsonify(perguntas), 200
        
    except (json.JSONDecodeError, ValueError) as e:
        print(f"🚨 Erro ao processar JSON da IA: {e}. Tentando contingência do Firebase...")
        
        # 4. Segundo ponto de contingência (JSON inválido)
        perguntas_reservas = obter_perguntas_reservas(db_client,nivel, tema_solicitado, num_perguntas)
        
        if perguntas_reservas:
            return jsonify(perguntas_reservas), 200
        else:
            return jsonify({"erro": f"Erro ao processar a resposta da IA: {e} e o banco de perguntas de reserva está indisponível ou vazio.", "resposta_bruta": resposta_groq}), 500

# ----------------------------------------------------------------------
# 🔹 Rota para verificar resposta
# ----------------------------------------------------------------------
@vialactea_bp.route('/verificar', methods=['POST'])
def verificar_resposta():
    dados = request.json
    pergunta = dados.get("pergunta", "")
    alternativas = dados.get("alternativas", {})
    resposta_usuario = dados.get("resposta", "")
    explicacao_texto = dados.get("explicacao", "")
    if not pergunta or not alternativas or not resposta_usuario:
        return jsonify({"erro": "Dados incompletos"}), 400
    
    pergunta_completa = pergunta + "\n\n"
    for letra, texto in alternativas.items():
        pergunta_completa += f"{letra}) {texto}\n"
    
    resposta_correta = dados.get("resposta", "").strip().upper()
    resposta_usuario = resposta_usuario.strip().upper()
    
    prompt = (
        f"Aqui está uma pergunta de português:\n\n{pergunta_completa}\n"
        f"Resposta correta: {resposta_correta}\n"
        f"O usuário escolheu: {resposta_usuario}\n"
        f"Avalie se ele acertou ou errou, se ele errou retorne a {resposta_correta} e o {explicacao_texto} de forma simples e didática.\n"
        f"Use linguagem clara e adequada ao ensino médio."
        f"Se a resposta estiver correta, retorne 'Correto'. Se estiver errada, retorne 'Incorreto'."
        f"Evite usar frases longas ou complexas. "
    )
    
    resposta, status = chamar_groq(prompt, "Você é um corretor experiente de provas de Língua Portuguesa. Avalie a resposta do aluno.")
    
    if not resposta:
        return jsonify({"erro": "Erro ao verificar resposta"}), status
        
    return jsonify({
        "avaliacao": resposta,
        "correta": resposta_usuario == resposta_correta
    }), 200