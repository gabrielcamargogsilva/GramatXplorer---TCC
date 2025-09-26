from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import json
import re
import sys
import firebase_admin
from firebase_admin import credentials, firestore
import random 
from dotenv import load_dotenv


load_dotenv()

try:
    FBKEY = json.loads(os.getenv('CONFIG_FIREBASE'))
    cred = credentials.Certificate(FBKEY)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Conectado ao Firebase com sucesso!")
except Exception as e:
    print(f"❌ Erro ao conectar ao Firebase: {e}")
    sys.exit()


app = Flask(__name__)
CORS(app)
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# 🔹 Estrutura de dados para as trilhas de atividades
trilhas_de_atividades = {
    'via_lactea': {
        'via_lactea_fase_1': {'nome': 'Galáxia Via Láctea', 'tema': 'revisao_geral'},
    },
    'andromeda': {
        'andromeda_fase_1': {'nome': 'Galáxia Andrômeda', 'tema': 'revisao_geral'},
    },
}

# 🔹 Estruturas de metas de pontos por trilha
metas_pontuacao_via_lactea = {
    1: {'meta': 990, 'nome': 'Netuno', 'tema': 'sintaxe'},
    2: {'meta': 2000, 'nome': 'Urano', 'tema': 'morfologia'},
    3: {'meta': 3500, 'nome': 'Saturno', 'tema': 'pragmatica'},
    4: {'meta': 5000, 'nome': 'Júpiter', 'tema': 'revisao_geral'},
    5: {'meta': 7500, 'nome': 'Terra', 'tema': 'revisao_geral'},
}

metas_pontuacao_andromeda = {
    1: {'meta': 990, 'nome': 'Sirius'},
    2: {'meta': 2000, 'nome': 'Betelgeuse'},
    3: {'meta': 3500, 'nome': 'Vega'},
    4: {'meta': 5000, 'nome': 'Proxima Centauri'},
    5: {'meta': 7500, 'nome': 'Kepler-186f'},
}

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
        response.raise_for_status()
        resposta = response.json()
        return resposta['choices'][0]['message']['content'].strip(), 200
    except requests.exceptions.RequestException as e:
        print(f"Erro ao chamar Groq API: {e}")
        return None, 500

# 🔹 Rota para obter as fases de um jogo específico
@app.route('/fases/<jogo>', methods=['GET'])
def get_fases_do_jogo(jogo):
    if jogo not in trilhas_de_atividades:
        return jsonify({"erro": "Jogo não encontrado."}), 404
    return jsonify(trilhas_de_atividades[jogo]), 200

# 🔹 Rota para obter o progresso de um usuário em um jogo
@app.route('/progresso/<usuario_id>/<jogo>', methods=['GET'])
def get_progresso_do_jogo(usuario_id, jogo):
    aluno_ref = db.collection('alunos').document(usuario_id)
    aluno_doc = aluno_ref.get()
    
    progresso_do_jogo = None
    if aluno_doc.exists:
        aluno_data = aluno_doc.to_dict()
        progresso_do_jogo = aluno_data.get('progresso', {}).get(jogo)

    if not progresso_do_jogo:
        primeira_fase = list(trilhas_de_atividades[jogo].keys())[0]
        progresso_do_jogo = {
            'pontuacao_total': 0,
            'nivel': 1,
            'fase_atual': primeira_fase,
            'estrelas_por_fase': {}
        }
        aluno_ref.set({'progresso': {}}, merge=True)
        aluno_ref.update({
            f'progresso.{jogo}': progresso_do_jogo
        })

    if jogo == 'andromeda':
        progresso_do_jogo['nome_planeta_atual'] = metas_pontuacao_andromeda.get(progresso_do_jogo['nivel'], {}).get('nome', 'Sirius')
    elif jogo == 'via_lactea':
        progresso_do_jogo['nome_planeta_atual'] = metas_pontuacao_via_lactea.get(progresso_do_jogo['nivel'], {}).get('nome', 'Netuno')

    return jsonify(progresso_do_jogo), 200

# 🔹 Rota para pontuar uma atividade de um jogo
@app.route('/progresso/<usuario_id>/<jogo>/pontuar', methods=['POST'])
def pontuar_atividade_do_jogo(usuario_id, jogo):
    dados = request.json
    fase = dados.get('fase')
    estrelas = dados.get('estrelas')

    if not usuario_id or not jogo or not fase or estrelas is None or estrelas < 0 or estrelas > 3:
        return jsonify({"erro": "Dados inválidos."}), 400

    aluno_ref = db.collection('alunos').document(usuario_id)
    aluno_doc = aluno_ref.get()
    
    if not aluno_doc.exists:
        return jsonify({"erro": "Aluno não encontrado."}), 404
    
    progresso_do_jogo = aluno_doc.to_dict().get('progresso', {}).get(jogo)

    if not progresso_do_jogo:
        return jsonify({"erro": "Progresso do jogo não encontrado. Chame a rota GET /progresso primeiro."}), 404

    pontos_ganhos = estrelas * 100
    nova_pontuacao = progresso_do_jogo['pontuacao_total'] + pontos_ganhos
    
    metas = {}
    if jogo == 'andromeda':
        metas = metas_pontuacao_andromeda
    elif jogo == 'via_lactea':
        metas = metas_pontuacao_via_lactea
    
    novo_nivel = 1
    niveis_ordenados = sorted(metas.keys())
    for nivel_alvo in niveis_ordenados:
        meta_requerida = metas[nivel_alvo]['meta']
        if nova_pontuacao >= meta_requerida:
            novo_nivel = nivel_alvo + 1
        else:
            break
    
    update_data = {
        'pontuacao_total': nova_pontuacao,
        'nivel': novo_nivel,
        'estrelas_por_fase': {**progresso_do_jogo['estrelas_por_fase'], **{fase: estrelas}}
    }
    
    aluno_ref.update({
        f'progresso.{jogo}': update_data
    })

    nome_planeta = ''
    if jogo == 'andromeda':
        nome_planeta = metas_pontuacao_andromeda.get(novo_nivel, {}).get('nome', 'Sirius')
    elif jogo == 'via_lactea':
        nome_planeta = metas_pontuacao_via_lactea.get(novo_nivel, {}).get('nome', 'Netuno')

    return jsonify({
        "mensagem": f"Pontuação atualizada em {jogo}. {pontos_ganhos} pontos adicionados.",
        "pontuacao_total": nova_pontuacao,
        "nivel_atual": novo_nivel,
        "estrelas_da_fase": estrelas,
        "nome_planeta": nome_planeta
    }), 200


# ----------------------------------------------------------------------
# 🔹 NOVO CÓDIGO: Função de contingência do Firebase
# ----------------------------------------------------------------------
def obter_perguntas_reservas(nivel: str, tema: str, limite: int):
    """
    Busca perguntas de reserva no Firebase (coleção 'perguntas_reservas')
    filtrando por nível e tema como plano de contingência.
    """
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


# ----------------------------------------------------------------------
# 🔹 Rota para gerar perguntas (COM LÓGICA DE CONTINGÊNCIA)
# ----------------------------------------------------------------------
@app.route('/vialactea/perguntas', methods=['GET'])
def gerar_perguntas():
    nivel = request.args.get('nivel', 'medio').lower()
    tema_solicitado = request.args.get('tema', '').lower()
    num_perguntas = 12

    if nivel not in ['facil', 'medio', 'dificil']:
        return jsonify({"erro": "Nível inválido. Use: fácil, médio ou difícil."}), 400
        
    temas_disponiveis = {
        'sintaxe': 'Sintaxe, com foco em Sujeito e Predicado (tipos, concordância), e Objetos Direto e Indireto (diferenciação, uso da preposição). Inclua exemplos práticos para identificar essas funções.',
        'pragmatica': "Pragmática, abordando principalmente Atos de Fala (diretos/indiretos), Ironia e Humor (como são construídos), Regras de cortesia, Pressuposição, Dêixis e Implicatura (o que se subentende). A questão deve exigir interpretação de contexto.",
        'morfologia': "Morfologia, com foco em Radical, Afixos (prefixos e sufixos), Vogal Temática e Desinências na formação e flexão das palavras. Pergunte sobre a estrutura das palavras ou sua classificação morfológica.",
        'revisao_geral': "Revise os conceitos de sintaxe, morfologia e pragmática, focando na identificação de erros de concordância, regência, crase e pontuação. As questões devem apresentar textos com desvios gramaticais para o aluno corrigir ou identificar o erro."
    }

    if not tema_solicitado:
        return jsonify({"erro": "O parâmetro 'tema' é obrigatório para gerar as perguntas."}), 400
        
    tema_para_prompt = temas_disponiveis.get(tema_solicitado)
    if not tema_para_prompt:
        return jsonify({"erro": "Tema inválido. Temas disponíveis: " + ', '.join(temas_disponiveis.keys())}), 400

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
        "     \"pergunta\": \"texto da pergunta\",\n"
        "     \"alternativas\": {\"A\": \"texto da alt. A\", \"B\": \"texto da alt. B\", \"C\": \"texto da alt. C\", \"D\": \"texto da alt. D\"},\n"
        "     \"resposta\": \"letra da resposta correta (A, B, C ou D)\",\n"
        "     \"subtema\": \"subtema da gramática\",\n"
        "     \"explicacao\": \"justificativa da resposta correta\"\n"
        "}\n\n"
        "Exemplo de como o retorno deve ser:\n"
        "[\n"
        "   {\n"
        "     \"pergunta\": \"Qual é a função sintática do termo 'o livro' na frase 'João comprou o livro'?\",\n"
        "     \"alternativas\": {\"A\": \"Sujeito\", \"B\": \"Objeto Direto\", \"C\": \"Objeto Indireto\", \"D\": \"Adjunto Adnominal\"},\n"
        "     \"resposta\": \"B\",\n"
        "     \"subtema\": \"Objeto Direto\",\n"
        "     \"explicacao\": \"O termo 'o livro' completa o sentido do verbo transitivo direto 'comprou', sem preposição, funcionando como Objeto Direto.\"\"\n"
        "   },\n"
        "   ...\n"
        "]"
    )
    
    # 1. Tenta chamar a IA (Groq)
    resposta_groq, status = chamar_groq(prompt, "Você é um professor de português criando um quiz de múltipla escolha. Retorne as questões em JSON.")
    
    # 2. Lógica de Contingência: Se a chamada falhar (ex: status != 200, limite estourado, ou resposta None)
    if not resposta_groq or status != 200:
        print(f"🚨 Falha na Groq API (Status: {status}). Ativando plano de contingência do Firebase...")
        
        # Chama a função para obter perguntas de reserva
        perguntas_reservas = obter_perguntas_reservas(nivel, tema_solicitado, num_perguntas)

        if perguntas_reservas:
            # Sucesso no plano de contingência, retorna as perguntas do Firebase
            return jsonify(perguntas_reservas), 200
        else:
            # Falha na IA E no Firebase
            return jsonify({"erro": "Erro na chamada da Groq API e o banco de perguntas de reserva está indisponível ou vazio para o tema/nível solicitado."}), 503 # Service Unavailable

    # 3. Processamento normal da resposta da IA
    try:
        resposta_limpa = resposta_groq.strip().lstrip('`json\n').lstrip('`python\n').rstrip('`')
        perguntas = json.loads(resposta_limpa)
        
        # Validação do formato JSON
        if not isinstance(perguntas, list):
            raise ValueError(f"A resposta da IA não é uma lista.")
        for p in perguntas:
            if not all(k in p for k in ["pergunta", "alternativas", "resposta", "subtema", "explicacao"]):
                raise ValueError("Uma das perguntas está incompleta.")
            if not isinstance(p.get("alternativas"), dict) or len(p.get("alternativas", {})) != 4:
                raise ValueError("O campo 'alternativas' não é um dicionário com 4 itens.")
            if not p.get("resposta") in ["A", "B", "C", "D"]:
                raise ValueError("A resposta correta não é A, B, C ou D.")
                
        for i, pergunta in enumerate(perguntas):
            pergunta['id'] = i + 1 # Atribui IDs sequenciais para as perguntas da IA
            
        return jsonify(perguntas), 200
        
    except (json.JSONDecodeError, ValueError) as e:
        print(f"🚨 Erro ao processar JSON da IA: {e}. Tentando contingência do Firebase...")
        
        # 4. Segundo ponto de contingência: Se o JSON da IA for inválido, usa o Firebase
        perguntas_reservas = obter_perguntas_reservas(nivel, tema_solicitado, num_perguntas)
        
        if perguntas_reservas:
            return jsonify(perguntas_reservas), 200
        else:
            # Falha na IA (JSON) E no Firebase
            return jsonify({"erro": f"Erro ao processar a resposta da IA: {e} e o banco de perguntas de reserva está indisponível ou vazio para o tema/nível solicitado.", "resposta_bruta": resposta_groq}), 500
# ----------------------------------------------------------------------
# Fim da Rota /vialactea/perguntas
# ----------------------------------------------------------------------


@app.route('/vialactea/verificar', methods=['POST'])
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