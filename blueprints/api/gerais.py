# api/gerais.py

from flask import Blueprint, request, jsonify, current_app
from config_data import trilhas_de_atividades, metas_pontuacao_via_lactea, metas_pontuacao_andromeda
# Importa o 'db' do Firebase que foi inicializado no app.py


gerais_bp = Blueprint('gerais', __name__)

# 🔹 Rota para obter as fases de um jogo específico
@gerais_bp.route('/fases/<jogo>', methods=['GET'])
def get_fases_do_jogo(jogo):
    if jogo not in trilhas_de_atividades:
        return jsonify({"erro": "Jogo não encontrado."}), 404
    return jsonify(trilhas_de_atividades[jogo]), 200

# 🔹 Rota para obter o progresso de um usuário em um jogo
@gerais_bp.route('/progresso/<usuario_id>/<jogo>', methods=['GET'])
def get_progresso_do_jogo(usuario_id, jogo):
    db_client = current_app.config.get('DB')
    if not db_client:
        return jsonify({"erro": "Serviço de banco de dados indisponível."}), 503
        
    aluno_ref = db_client.collection('alunos').document(usuario_id)
    aluno_doc = aluno_ref.get()
    
    progresso_do_jogo = None
    if aluno_doc.exists:
        aluno_data = aluno_doc.to_dict()
        progresso_do_jogo = aluno_data.get('progresso', {}).get(jogo)

    if not progresso_do_jogo:
        if jogo not in trilhas_de_atividades:
            return jsonify({"erro": "Jogo não encontrado."}), 404
        
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
@gerais_bp.route('/progresso/<usuario_id>/<jogo>/pontuar', methods=['POST'])
def pontuar_atividade_do_jogo(usuario_id, jogo):
    db_client = current_app.config.get('DB')

    if not db_client:
        return jsonify({"erro": "Serviço de banco de dados indisponível."}), 503
        
    dados = request.json
    fase = dados.get('fase')
    estrelas = dados.get('estrelas')

    if not usuario_id or not jogo or not fase or estrelas is None or estrelas < 0 or estrelas > 3:
        return jsonify({"erro": "Dados inválidos."}), 400

    aluno_ref = db_client.collection('alunos').documment(usuario_id)
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
    
    # Atualiza o progresso
    update_data = {
        'pontuacao_total': nova_pontuacao,
        'nivel': novo_nivel,
        'estrelas_por_fase': {**progresso_do_jogo.get('estrelas_por_fase', {}), **{fase: estrelas}}
    }
    
    # Prepara o objeto para atualização no Firebase
    firebase_update = {
        f'progresso.{jogo}.{k}': v for k, v in update_data.items()
    }
    aluno_ref.update(firebase_update)


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