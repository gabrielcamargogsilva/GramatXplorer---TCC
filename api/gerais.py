from flask import Blueprint, request, jsonify, current_app
from config_data import trilhas_de_atividades, metas_pontuacao_via_lactea, metas_pontuacao_andromeda


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

    if not aluno_doc.exists:
        return jsonify({"erro": "Aluno não encontrado."}), 404

    aluno_data = aluno_doc.to_dict()

    # ✅ CORREÇÃO 1: Busca o progresso aninhado em 'processo'
    progresso_do_jogo = aluno_data.get('processo', {}).get(jogo)

    if not progresso_do_jogo:
        # Se o progresso não existir (o que só deve acontecer se o documento foi criado 
        # sem a estrutura padrão ou houve erro), retorna um erro.
        return jsonify({"erro": f"Progresso do jogo '{jogo}' não encontrado no campo 'processo'. Estrutura de dados ausente."}), 404
        
    # --- LÓGICA DE INICIALIZAÇÃO REMOVIDA ---

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
    estrelas_raw = dados.get('estrelas')
    
    estrelas = None
    
    # Tenta converter 'estrelas' para int para evitar TypeError
    try:
        estrelas = int(estrelas_raw) if estrelas_raw is not None else None
    except ValueError:
        return jsonify({"erro": "O valor de 'estrelas' deve ser um número inteiro válido (0 a 3)."}), 400


    # Validação
    if not usuario_id or not jogo or not fase or estrelas is None or estrelas < 0 or estrelas > 3:
        return jsonify({"erro": "Dados inválidos: Verifique usuario_id, jogo, fase e estrelas (0-3)."}), 400

    aluno_ref = db_client.collection('alunos').document(usuario_id)
    aluno_doc = aluno_ref.get()

    if not aluno_doc.exists:
        return jsonify({"erro": "Aluno não encontrado."}), 404

    # ✅ CORREÇÃO 2: Busca o progresso aninhado em 'processo'
    progresso_do_jogo = aluno_doc.to_dict().get('processo', {}).get(jogo)

    if not progresso_do_jogo:
        return jsonify({"erro": f"Progresso do jogo '{jogo}' não encontrado no campo 'processo'. Estrutura de dados ausente."}), 404

    pontos_ganhos = estrelas * 100
    nova_pontuacao = progresso_do_jogo.get('pontuacao_total', 0) + pontos_ganhos

    metas = {}
    if jogo == 'andromeda':
        metas = metas_pontuacao_andromeda
    elif jogo == 'via_lactea':
        metas = metas_pontuacao_via_lactea

    novo_nivel = progresso_do_jogo.get('nivel', 1) # Mantém o nível atual como padrão
    niveis_ordenados = sorted(metas.keys())
    
    # Lógica para determinar o novo nível
    for nivel_alvo in niveis_ordenados:
        meta_requerida = metas[nivel_alvo]['meta']
        
        if nova_pontuacao >= meta_requerida:
            novo_nivel = nivel_alvo 
            
            if nivel_alvo + 1 in metas:
                 novo_nivel = nivel_alvo + 1
            else:
                 novo_nivel = nivel_alvo 
        else:
            break
            
    # O objeto progressos_do_jogo é totalmente reconstruído
    update_data = {
        'pontuacao_total': nova_pontuacao,
        'nivel': novo_nivel,
        'fase_atual': fase, 
        # Atualiza ou adiciona as estrelas para a fase específica
        'estrelas_por_fase': {
            **progresso_do_jogo.get('estrelas_por_fase', {}), 
            fase: estrelas
        }
    }

    # ✅ CORREÇÃO 3: Atualiza o campo 'processo.<jogo>' usando a notação de ponto
    # Para atualizar o mapa aninhado sem recriar o campo superior 'processo' ou 'aluno', 
    # precisamos usar a notação de ponto para o caminho completo.
    firebase_update = {
        f'processo.{jogo}.{k}': v for k, v in update_data.items()
    }
    
    aluno_ref.update(firebase_update)
    
    # O restante do código prepara a resposta JSON
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