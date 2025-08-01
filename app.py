from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import json
import re

app = Flask(__name__)
CORS(app)
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# 🔹 Rota raiz
@app.route('/')
def home():
    return "<h1>API está on</h1>"


def chamar_groq(mensagem_user, mensagem_sistema=""):
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
        response.raise_for_status() # Isso levantará um erro HTTP para status codes 4xx/5xx
        resposta = response.json()
        return resposta['choices'][0]['message']['content'].strip(), 200
    except requests.exceptions.RequestException as e:
        print(f"Erro ao chamar Groq API: {e}")
        return None, 500 # Retorna None e um status de erro em caso de falha


@app.route('/vialactea/perguntas', methods=['GET'])
def gerar_perguntas():
    nivel = request.args.get('nivel', 'médio').lower()
    tema_solicitado = request.args.get('tema', '').lower()
    num_perguntas = 12 # Mantendo o número original, mas o código agora é mais flexível

    if nivel not in ['facil', 'medio', 'dificil']:
        return jsonify({"erro": "Nível inválido. Use: fácil, médio ou difícil."}), 400

    temas_disponiveis = {
        'sintaxe': 'Sintaxe, com foco em Sujeito e Predicado (tipos, concordância), e Objetos Direto e Indireto (diferenciação, uso da preposição). Inclua exemplos práticos para identificar essas funções.',
        'pragmatica': "Pragmática, abordando principalmente Atos de Fala (diretos/indiretos), Ironia e Humor (como são construídos), Regras de cortesia, Pressuposição, Dêixis e Implicatura (o que se subentende). A questão deve exigir interpretação de contexto.",
        'morfologia': "Morfologia, com foco em Radical, Afixos (prefixos e sufixos), Vogal Temática e Desinências na formação e flexão das palavras. Pergunte sobre a estrutura das palavras ou sua classificação morfológica.",
    }

    tema_para_prompt = ""
    if tema_solicitado and tema_solicitado in temas_disponiveis:
        tema_para_prompt = temas_disponiveis[tema_solicitado]

    contexto_dificuldade = {
        'facil': "Elabore a pergunta com vocabulário mais simples, com foco em conteúdos básicos e exemplos acessíveis.",
        'medio': "Use nível intermediário de complexidade, com exemplos contextualizados e exigência razoável de análise.",
        'dificil': "Inclua maior profundidade e complexidade na pergunta, exigindo maior domínio das regras gramaticais e interpretação sutil."
    }

    prompt = (
        f"Você é um professor experiente de Língua Portuguesa voltado para o ensino médio. "
        f"Crie {num_perguntas} questões de gramática contextualizadas, de múltipla escolha, com 4 alternativas (A, B, C, D), sendo apenas uma correta. "
        f"A dificuldade deve ser de nível '{nivel}'. {contexto_dificuldade[nivel]} "
        f"As questões devem abordar conteúdos como: {tema_para_prompt} "
        "Para cada questão, forneça o subtema específico e uma explicação concisa e direta, focada apenas na justificativa da resposta. "
        "Retorne a resposta em um formato JSON, sendo um array de objetos. "
        "Não inclua qualquer texto antes ou depois do JSON. "
        "O formato de cada objeto JSON deve ser o seguinte:\n"
        "{\n"
        "    \"pergunta\": \"texto da pergunta\",\n"
        "    \"alternativas\": {\"A\": \"texto da alt. A\", \"B\": \"texto da alt. B\", \"C\": \"texto da alt. C\", \"D\": \"texto da alt. D\"},\n"
        "    \"resposta\": \"letra da resposta correta (A, B, C ou D)\",\n"
        "    \"subtema\": \"subtema da gramática\",\n"
        "    \"explicacao\": \"justificativa da resposta correta\"\n"
        "}\n\n"
        "Exemplo de como o retorno deve ser:\n"
        "[\n"
        "  {\n"
        "    \"pergunta\": \"Qual é a função sintática do termo 'o livro' na frase 'João comprou o livro'?\",\n"
        "    \"alternativas\": {\"A\": \"Sujeito\", \"B\": \"Objeto Direto\", \"C\": \"Objeto Indireto\", \"D\": \"Adjunto Adnominal\"},\n"
        "    \"resposta\": \"B\",\n"
        "    \"subtema\": \"Objeto Direto\",\n"
        "    \"explicacao\": \"O termo 'o livro' completa o sentido do verbo transitivo direto 'comprou', sem preposição, funcionando como Objeto Direto.\"\n"
        "  },\n"
        "  ...\n"
        "]"
    )

    resposta_groq, status = chamar_groq(prompt, "Você é um professor de português criando um quiz de múltipla escolha. Retorne as questões em JSON.")

    if not resposta_groq:
        return jsonify({"erro": "Erro na chamada da Groq API."}), status

    try:
        # A IA pode retornar o JSON dentro de um bloco de código Markdown
        # Removemos `json` e `python` do início e fim para garantir
        resposta_limpa = resposta_groq.strip().lstrip('`json\n').lstrip('`python\n').rstrip('`')
        perguntas = json.loads(resposta_limpa)
        
       
        if not isinstance(perguntas, list):
            raise ValueError(f"A resposta da IA não é uma lista.")

        # Validação mais robusta de cada pergunta
        for p in perguntas:
            if not all(k in p for k in ["pergunta", "alternativas", "resposta", "subtema", "explicacao"]):
                raise ValueError("Uma das perguntas está incompleta.")
            if not isinstance(p.get("alternativas"), dict) or len(p.get("alternativas", {})) != 4:
                raise ValueError("O campo 'alternativas' não é um dicionário com 4 itens.")
            if not p.get("resposta") in ["A", "B", "C", "D"]:
                raise ValueError("A resposta correta não é A, B, C ou D.")
            

        for i, pergunta in enumerate(perguntas):
            pergunta['id'] = i + 1
        
        return jsonify(perguntas), 200

    except (json.JSONDecodeError, ValueError) as e:
        print(f"Erro ao processar JSON da IA: {e}")
        return jsonify({"erro": f"Erro ao processar a resposta da IA: {e}", "resposta_bruta": resposta_groq}), 500


# O restante das rotas fica inalterado

@app.route('/vialactea/verificar', methods=['POST'])
def verificar_resposta():
    # ... (código inalterado)
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


@app.route('/andromeda/texto_usuario', methods=['GET'])
def gerar_texto_com_erros():
    # ... (código inalterado)
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

@app.route('/andromeda/correcao', methods=['POST'])
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
        "Avalie a correção do aluno seguindo as instruções abaixo:\\n"
        "1. Liste os erros corrigidos corretamente (máximo 4 linhas).\\n"
        "2. Liste os erros que permanecem ou foram corrigidos de forma errada (máximo 4 linhas).\\n"
        "3. Explique de forma bem didática e simples, sem usar palavras difíceis ou jargões técnicos.\\n"
        "4. Informe apenas o número de erros corrigidos corretamente e o número de erros que permanecem ou foram corrigidos de forma errada.\\n"
        "Devolva no formato JSON se acordo com o modelo:\\n"
        "{{
        "   \"corretos\": [\"lista de erros corrigidos corretamente, cada item uma string\"],\\n"
        "   \"incorretos\": [\"lista de erros que permanecem ou foram corrigidos de forma errada, cada item uma string\"],\\n"
        "   \"explicacao\": \"explicação didática, simples e resumida\",\\n"
        "   \"erros_corrigidos\": 2,\\n"
        "   \"erros_incorretos\": 3\\n"
        "}}\\n\\n"
        "As chaves 'corretos' e 'incorretos' devem ser listas de strings, onde cada string descreve um erro."
        "6. A explicação deve ser curta e clara, como se estivesse ensinando para um aluno do ensino médio.\\n"
        "7. Não use frases longas, complexas ou técnicas.\\n"
        "8. Não escreva nada fora do JSON."
    """

    resposta, status = chamar_groq(prompt, "Você é um professor corrigindo redações de alunos. Avalie a correção do aluno. Seja didático. Use linguagem clara e adequada ao ensino médio.")

    if not resposta:
        return jsonify({"erro": "Erro ao avaliar correção"}), status

    try:
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


if __name__ == '__main__':
    app.run(debug=True)