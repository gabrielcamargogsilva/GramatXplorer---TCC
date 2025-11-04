from flask import Blueprint, jsonify, request, current_app


admin_bp = Blueprint('admin', __name__)

# NOTA: O prefixo /admin será adicionado no app.py, então a rota completa será /admin/alunos

# ====================================================================
# 🔹 ROTA 1: Listar Todos os Alunos
# ====================================================================
@admin_bp.route('/alunos', methods=['GET'])
def listar_alunos():
    db_client = current_app.config.get('DB')

    if not db_client:
        return jsonify({"erro": "Serviço de banco de dados indisponível."}), 503

    alunos = []
    try:
        # Busca todos os documentos na coleção 'alunos'
        docs = db_client.collection('alunos').stream()
        
        for doc in docs:
            aluno_data = doc.to_dict()
            
            # Garante que o ID do aluno (nome do documento) esteja incluído
            aluno = {
                'id': doc.id,
                'nome': aluno_data.get('nome', 'Nome Desconhecido'),
                'email': aluno_data.get('email', 'Email Desconhecido'),
                'ativo': aluno_data.get('ativo','vazio')
            }
            alunos.append(aluno)

        return jsonify(alunos), 200
    except Exception as e:
        print(f"Erro ao listar alunos: {e}")
        return jsonify({"erro": f"Erro interno ao listar alunos: {e}"}), 500

# ====================================================================
# 🔹 ROTA 2: Ativar ou Desativar Aluno (Alterar Status)      # tem que arrumar esta rota 
# ====================================================================
@admin_bp.route('/alunos/<aluno_id>/status', methods=['PUT'])
def alterar_status_aluno(aluno_id):
    db_client = current_app.config.get('DB')

    if not db_client:
        return jsonify({"erro": "Serviço de banco de dados indisponível."}), 503
        
    dados = request.json
    novo_status = dados.get('ativo')

    if novo_status is None or not isinstance(novo_status, bool):
        return jsonify({"erro": "O campo 'ativo' (booleano) é obrigatório."}), 400
    
    aluno_ref = db_client.collection('alunos').document(aluno_id)

    try:
        if not aluno_ref.get().exists:
            print(f"DEBUG: Aluno ID {aluno_id} não encontrado no DB.")
            return jsonify({"erro": "Aluno não encontrado."}), 404
            
        print(f"DEBUG: Tentando atualizar aluno {aluno_id} para ativo={novo_status}") # <-- NOVO LOG
        
        aluno_ref.update({'ativo': novo_status})

        print(f"DEBUG: Aluno {aluno_id} atualizado com sucesso!") # <-- NOVO LOG
        
        acao = "ativado" if novo_status else "desativado"
        return jsonify({"mensagem": f"Aluno {aluno_id} foi {acao} com sucesso.", "ativo": novo_status}), 200
    except Exception as e:
        print(f"ERRO CRÍTICO DB: {e}") # <-- LOG MAIS VISÍVEL PARA O ERRO
        return jsonify({"erro": f"Erro ao atualizar status do aluno: {e}"}), 500


# ====================================================================
# 🔹 ROTA 3: Excluir Aluno
# ====================================================================
@admin_bp.route('/alunos/<aluno_id>', methods=['DELETE'])
def excluir_aluno(aluno_id):
    db_client = current_app.config.get('DB')

    if not db_client:
        return jsonify({"erro": "Serviço de banco de dados indisponível."}), 503
        
    aluno_ref = db_client.collection('alunos').document(aluno_id)

    try:
        # Verifica se o aluno existe antes de tentar excluir
        if not aluno_ref.get().exists:
            return jsonify({"erro": "Aluno não encontrado."}), 404

        aluno_ref.delete()
        
        return jsonify({"mensagem": f"Aluno {aluno_id} excluído com sucesso."}), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao excluir aluno: {e}"}), 500