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

@app.route('/vialactea/pergunta', methods=['GET'])
def gerar_pergunta():
    nivel = request.args.get('nivel', 'médio').lower()
    tema_solicitado = request.args.get('tema', '').lower()

    if nivel not in ['facil', 'medio', 'dificil']:
        return jsonify({"erro": "Nível inválido. Use: fácil, médio ou difícil."}), 400

    temas_disponiveis = {
        'sintaxe': 'Sintaxe, com foco em **Sujeito e Predicado** (tipos, concordância), e **Objetos Direto e Indireto** (diferenciação, uso da preposição). Inclua exemplos práticos para identificar essas funções.',
        'pragmatica': "Pragmática, abordando principalmente **Atos de Fala** (diretos/indiretos), **Ironia e Humor** (como são construídos), **Regras de cortesia**, **Pressuposição**, **Dêixis** e **Implicatura** (o que se subentende). A questão deve exigir interpretação de contexto.",
        'morfologia': "Morfologia, com foco em **Radical, Afixos (prefixos e sufixos), Vogal Temática e Desinências** na formação e flexão das palavras. Pergunte sobre a estrutura das palavras ou sua classificação morfológica.",
    }

    tema_para_prompt = "" 
    if tema_solicitado and tema_solicitado in temas_disponiveis:
        tema_para_prompt = temas_disponiveis[tema_solicitado]
    
    contexto_dificuldade = {
        'facil': "Elabore a pergunta com vocabulário mais simples, com foco em conteúdos básicos e exemplos acessíveis.",
        'medio': "Use nível intermediário de complexidade, com exemplos contextualizados e exigência razoável de análise.",
        'dificil': "Inclua maior profundidade e complexidade na pergunta, exigindo maior domínio das regras gramaticais e interpretação sutil."
    }

    ### Lógica de Retentativa

    max_tentativas = 5  
    tentativas = 0
    pergunta_valida = False
    
    pergunta_texto = "Pergunta não encontrada"
    alternativas = {}
    letra_resposta = ""
    subtema_texto = "" 
    explicacao_texto = ""

    while not pergunta_valida and tentativas < max_tentativas:
        prompt = (
            f"{contexto_dificuldade[nivel]}\n\n"
            "Você é um professor experiente de Língua Portuguesa voltado para o ensino médio. "
            "Crie uma questão de gramática contextualizada, de múltipla escolha, com 4 alternativas (A, B, C, D), sendo apenas uma correta. "
            f"A questão deve abordar conteúdos como: {tema_para_prompt} " 
            "Contextualize com uma frase ou pequeno trecho. "
            "Retorne a explicação de forma extremamente resumida e garanta que a explicação contenha apenas a justificativa da resposta, sem repetir a pergunta ou as alternativas.\n" 
            "Formato:\n\n"
            "Pergunta: ...\n"
            "A) ...\nB) ...\nC) ...\nD) ...\nResposta correta: ...\n"
            "Subtema: [O subtema específico da pergunta, por exemplo: Sujeito, Objeto Direto, Atos de Fala, Radical, Afixos, etc.]\n" # Instrução mais detalhada para o subtema
            "Explicação: ..."
            "Retorne sempre a resposta correta." 
        )

        resposta_groq, status = chamar_groq(prompt, "Você é um professor de português criando quiz de múltipla escolha.")
        
        if not resposta_groq:
            print(f"Erro na chamada da Groq na tentativa {tentativas + 1}.")
            break 

        # Extrair pergunta
        pergunta_match = re.search(r"Pergunta:\s*(.*?)(?=\nA\))", resposta_groq, re.DOTALL)
        pergunta_texto = pergunta_match.group(1).strip() if pergunta_match else ""

        # Extrair alternativas
        alternativas_match = re.findall(r"([ABCD])\)\s*(.*?)\n(?=[A-D]\)|Resposta correta:)", resposta_groq, re.DOTALL)
        alternativas = {letra: texto.strip() for letra, texto in alternativas_match}

        # Extrair letra da resposta correta
        resposta_match = re.search(r"Resposta correta:\s*([ABCD])", resposta_groq)
        letra_resposta = resposta_match.group(1).strip() if resposta_match else ""

        # --- Extrair Subtema com mais precisão ---
        # A regex deve ser o mais precisa possível para capturar APENAS o subtema
        subtema_match = re.search(r"Subtema:\s*(.*?)(?=\nExplicação:|\Z)", resposta_groq)
        subtema_texto = subtema_match.group(1).strip() if subtema_match else ""
        
        # Opcional: Limpar o subtema de possíveis ruídos, se a IA ainda incluir.
        # Por exemplo, se a IA retornar "Subtema: Sujeito (tipos)", e você quiser apenas "Sujeito"
        # subtema_texto = re.sub(r'\s*\(.*\)', '', subtema_texto).strip()

        # Extrair explicação com regex mais preciso (não-guloso)
        explicacao_match = re.search(r"Explicação:\s*(.*?)(?=\n\n|\Z)", resposta_groq, re.DOTALL)
        explicacao_texto = explicacao_match.group(1).strip() if explicacao_match else ""
        
        explicacao_texto = re.sub(r"A resposta correta é [ABCD]\).*", "", explicacao_texto).strip()

        # --- Validação da Pergunta ATUALIZADA para garantir que o subtema não está vazio ---
        if pergunta_texto and 'D' in alternativas and len(alternativas) == 4 and letra_resposta and subtema_texto:
            pergunta_valida = True
        else:
            # Melhorar a mensagem de log para indicar o que faltou, incluindo o subtema
            faltantes = []
            if not pergunta_texto: faltantes.append("Pergunta")
            if 'D' not in alternativas or len(alternativas) != 4: faltantes.append("Alternativas (A,B,C,D)")
            if not letra_resposta: faltantes.append("Resposta Correta")
            if not subtema_texto: faltantes.append("Subtema")
            
            print(f"Tentativa {tentativas + 1} falhou. Faltantes: {', '.join(faltantes)}. Resposta bruta da IA (trecho): \n---\n{resposta_groq[:300]}...\n---\nRetentando...")
            
            tentativas += 1
            
    if not pergunta_valida:
        return jsonify({"erro": "Não foi possível gerar uma pergunta válida após múltiplas tentativas. Tente novamente."}), 500

    for letra in ['A', 'B', 'C', 'D']:
        if letra not in alternativas:
            alternativas[letra] = "[alternativa não fornecida]"

    return jsonify({
        "nivel": nivel,
        "tema": tema_solicitado, 
        "pergunta": pergunta_texto,
        "alternativas": alternativas,
        "resposta": letra_resposta,
        "subtema": subtema_texto, 
        "explicacao": explicacao_texto
    }), 200



@app.route('/vialactea/verificar', methods=['POST'])
def verificar_resposta():
    dados = request.json
    pergunta = dados.get("pergunta", "")
    alternativas = dados.get("alternativas", {})
    resposta_usuario = dados.get("resposta", "")
    explicacao_texto = dados.get("explicacao", "")

    if not pergunta or not alternativas or not resposta_usuario:
        return jsonify({"erro": "Dados incompletos"}), 400

    # Montar a pergunta completa com as alternativas
    pergunta_completa = pergunta + "\n\n"
    for letra, texto in alternativas.items():
        pergunta_completa += f"{letra}) {texto}\n"

    resposta_correta = dados.get("resposta", "").strip().upper()
    resposta_usuario = resposta_usuario.strip().upper()

    # Montar prompt para avaliação
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
        f"Você é um professor corrigindo texto de alunos. Avalie a correção do aluno. Seja didático. Use linguagem clara e adequada ao ensino médio.\n\n"
        "Texto com erros:\n\n{texto_original}\n\n"
        "Texto corrigido pelo aluno:\n\n{texto_usuario}\n\n"
        "Avalie a correção do aluno seguindo as instruções abaixo:\n"
        "1. Liste os erros corrigidos corretamente (máximo 4 linhas).\n"
        "2. Liste os erros que permanecem ou foram corrigidos de forma errada (máximo 4 linhas).\n"
        "3. Explique de forma bem didática e simples, sem usar palavras difíceis ou jargões técnicos.\n"
        "4. Informe apenas o número de erros corrigidos corretamente e o número de erros que permanecem ou foram corrigidos de forma errada.\n"
        Devolva no formato JSON se acordo com o modelo:
                {{
                    "corretos": ["lista de erros corrigidos corretamente, cada item uma string"],
                    "incorretos": ["lista de erros que permanecem ou foram corrigidos de forma errada, cada item uma string"],
                    "explicacao": "explicação didática, simples e resumida",
                    "erros_corrigidos": 2,
                    "erros_incorretos": 3
                }}

                "As chaves 'corretos' e 'incorretos' devem ser listas de strings, onde cada string descreve um erro."
        "6. A explicação deve ser curta e clara, como se estivesse ensinando para um aluno do ensino médio.\n"
        "7. Não use frases longas, complexas ou técnicas.\n"
        "8. Não escreva nada fora do JSON."
            """


    resposta, status = chamar_groq(prompt, "Você é um professor corrigindo redações de alunos. Avalie a correção do aluno. Seja didático. Use linguagem clara e adequada ao ensino médio.")

    if not resposta:
        return jsonify({"erro": "Erro ao avaliar correção"}), status

    try:
        # Tenta encontrar o JSON na string bruta da resposta
        # Procura pelo primeiro '{' e o último '}'
        start_index = resposta.find('{')
        end_index = resposta.rfind('}')

        if start_index != -1 and end_index != -1 and start_index < end_index:
            # Extrai a substring que parece ser o JSON
            json_string = resposta[start_index : end_index + 1]
            # Tenta carregar o JSON
            return jsonify(json.loads(json_string)), 200
        else:
            # Se não conseguir encontrar um JSON válido, retorna o erro original
            return jsonify({"erro": "Não foi possível extrair um JSON válido da resposta da IA", "resposta_bruta": resposta}), 500

    except json.JSONDecodeError as e:
        # Se a IA não retornar JSON válido ou houver outro erro de decodificação
        return jsonify({"erro": f"Erro ao decodificar JSON: {e}", "resposta_bruta": resposta}), 500
    except Exception as e:
        # Captura outras exceções inesperadas
        return jsonify({"erro": f"Erro inesperado: {e}", "resposta_bruta": resposta}), 500


  

if __name__ == '__main__':
    app.run(debug=True)
