# api/andromeda.py

from flask import Blueprint, request, jsonify
import json
from utils.groq_firebase import chamar_groq

andromeda_bp = Blueprint('andromeda', __name__)

@andromeda_bp.route('/texto_usuario', methods=['GET'])
def gerar_texto_com_erros():
    prompt = (
        "Você é um professor de Língua Portuguesa criando um exercício com erros gramaticais. "
        "Crie um parágrafo curto (3 a 5 linhas), informal, com 4 a 6 erros. "
        "Os erros podem envolver figuras de linguagem, vozes, paralinguagem, variação linguística, morfologia, tempos verbais, sintaxe, conjunções e regência. "
        "Não corrija nem explique os erros. Apenas gere o texto com os desvios inseridos."
        "O texto deve ser informal, como se fosse uma conversa entre amigos. "
        "Não use palavras difíceis ou jargões técnicos. "
        "Retorne somente o texto com erros, sem mensagem ao usuário no final"
    )
    resposta, status = chamar_groq(prompt, "Você é um professor gerando textos com erros para correção de alunos.")
    if not resposta:
        return jsonify({"erro": "Erro ao gerar texto"}), status
    return jsonify({"texto_com_erros": resposta}), 200

@andromeda_bp.route('/correcao', methods=['POST'])
def analisar_correcao():
    dados = request.json
    texto_original = dados.get("original", "")
    texto_usuario = dados.get("correcao", "")
    if not texto_original or not texto_usuario:
        return jsonify({"erro": "Dados incompletos"}), 400
        
    prompt = f"""
        "Você é um professor corrigindo texto de alunos. Avalie a correção do aluno. Seja didático. Use linguagem clara e adequada ao ensino médio.\\n\\n"
        "Texto com erros:\\n\\n{texto_original}\\n\\n"
        "Texto corrigido pelo aluno:\\n\\n{texto_usuario}\\n\\n"
        # ... (Restante do prompt com a estrutura JSON, como no seu código original) ...
    """
    
    resposta, status = chamar_groq(prompt, "Você é um professor corrigindo redações de alunos. Avalie a correção do aluno. Seja didático. Use linguagem clara e adequada ao ensino médio.")
    
    if not resposta:
        return jsonify({"erro": "Erro ao avaliar correção"}), status
        
    try:
        # Lógica para extrair JSON da resposta da IA (como no seu código original)
        start_index = resposta.find('{')
        end_index = resposta.rfind('}')
        if start_index != -1 and end_index != -1 and start_index < end_index:
            json_string = resposta[start_index : end_index + 1]
            return jsonify(json.loads(json_string)), 200
        else:
            return jsonify({"erro": "Não foi possível extrair um JSON válido da resposta da IA", "resposta_bruta": resposta}), 500
            
    except json.JSONDecodeError as e:
        return jsonify({"erro": f"Erro ao decodificar JSON: {e}", "resposta_bruta": resposta}), 500
    except Exception as e:
        return jsonify({"erro": f"Erro inesperado: {e}", "resposta_bruta": resposta}), 500