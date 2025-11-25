from flask import Blueprint, jsonify, request, current_app, render_template
# Importações necessárias para JWT
from flask_jwt_extended import jwt_required, get_jwt
from functools import wraps

admin_bp = Blueprint('admin', __name__)

# ====================================================================
# 🔹 DECORATOR DE VERIFICAÇÃO DE CARGO
# ====================================================================

def verify_admin_role():
    """
    Decorator personalizado para verificar se o token JWT contém o cargo 'admin'.
    Se não for 'admin', retorna um erro 403.
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            # 1. Obtém todas as claims do token JWT (incluindo o 'cargo')
            claims = get_jwt()
            cargo_usuario = claims.get('cargo')
            
            # 2. Verifica se o cargo é 'admin'
            if cargo_usuario != 'admin':
                return jsonify({"msgerro": "Acesso não autorizado. Apenas administradores podem acessar esta área."}), 403
            
            # 3. Se for admin, executa a função original da rota
            return fn(*args, **kwargs)
        return decorator
    return wrapper

# ====================================================================
# 🔹 ROTA para renderizar o Painel (PROTEGIDA)
# ====================================================================
@admin_bp.route('/', methods=['GET'])
@jwt_required()   # Requer um token JWT válido
@verify_admin_role() # Verifica se o cargo dentro do token é 'admin'
def admin_page():
    # Se chegou aqui, o token é válido e o cargo é 'admin'
    return render_template('admin_alunos.html')

# ====================================================================
# 🔹 ROTA 1: Listar Todos os Alunos (PROTEGIDA)
# ====================================================================
@admin_bp.route('/alunos', methods=['GET'])
@jwt_required()
@verify_admin_role()
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
            aluno = {
                'id': doc.id,
                'nome': aluno_data.get('nome', 'Nome Desconhecido'),
                'email': aluno_data.get('email', 'Email Desconhecido'),
                'ativo': aluno_data.get('ativo', False)
            }
            alunos.append(aluno)

        return jsonify(alunos), 200
    except Exception as e:
        print(f"Erro ao listar alunos: {e}")
        return jsonify({"erro": f"Erro interno ao listar alunos: {e}"}), 500

# ====================================================================
# 🔹 ROTA 2: Ativar ou Desativar Aluno (PROTEGIDA)
# ====================================================================
@admin_bp.route('/alunos/<aluno_id>/status', methods=['PUT'])
@jwt_required()
@verify_admin_role()
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
            return jsonify({"erro": "Aluno não encontrado."}), 404

        aluno_ref.update({'ativo': novo_status})

        acao = "ativado" if novo_status else "desativado"
        return jsonify({"mensagem": f"Aluno {aluno_id} foi {acao} com sucesso.", "ativo": novo_status}), 200
    except Exception as e:
        print(f"ERRO CRÍTICO DB: {e}")
        return jsonify({"erro": f"Erro ao atualizar status do aluno: {e}"}), 500

# ====================================================================
# 🔹 ROTA 3: Excluir Aluno (PROTEGIDA)
# ====================================================================
@admin_bp.route('/alunos/<aluno_id>', methods=['DELETE'])
@jwt_required()
@verify_admin_role()
def excluir_aluno(aluno_id):
    db_client = current_app.config.get('DB')
    
    if not db_client:
        return jsonify({"erro": "Serviço de banco de dados indisponível."}), 503

    aluno_ref = db_client.collection('alunos').document(aluno_id)

    try:
        if not aluno_ref.get().exists:
            return jsonify({"erro": "Aluno não encontrado."}), 404

        aluno_ref.delete()

        return jsonify({"mensagem": f"Aluno {aluno_id} excluído com sucesso."}), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao excluir aluno: {e}"}), 500

# ====================================================================
# 🔹 ROTA 4: Alterar Email do Aluno (PROTEGIDA)
# ====================================================================
@admin_bp.route('/alunos/<aluno_id>/email', methods=['PUT'])
@jwt_required()
@verify_admin_role()
def alterar_email_aluno(aluno_id):
    db_client = current_app.config.get('DB')
    
    if not db_client:
        return jsonify({"erro": "Serviço de banco de dados indisponível."}), 503

    dados = request.json
    novo_email = dados.get('email')

    # 1. Validação
    if not novo_email:
        return jsonify({"erro": "O campo 'email' é obrigatório."}), 400
    
    # Validação simples de formato
    if "@" not in novo_email or "." not in novo_email:
        return jsonify({"erro": "Formato de e-mail inválido."}), 400
    
    aluno_ref = db_client.collection('alunos').document(aluno_id)

    try:
        # 2. Verifica se o aluno existe
        if not aluno_ref.get().exists:
            return jsonify({"erro": "Aluno não encontrado."}), 404

        # 3. Atualiza o email no Firestore
        aluno_ref.update({'email': novo_email})

        return jsonify({"mensagem": f"E-mail do aluno {aluno_id} alterado para {novo_email} com sucesso."}), 200
        
    except Exception as e:
        print(f"ERRO CRÍTICO DB: {e}")
        return jsonify({"erro": f"Erro ao atualizar e-mail do aluno: {e}"}), 500

# ====================================================================
# 🆕 🔹 ROTA 5: Alterar Nome do Aluno (PROTEGIDA)
# ====================================================================
@admin_bp.route('/alunos/<aluno_id>/nome', methods=['PUT'])
@jwt_required()
@verify_admin_role()
def alterar_nome_aluno(aluno_id):
    db_client = current_app.config.get('DB')
    
    if not db_client:
        return jsonify({"erro": "Serviço de banco de dados indisponível."}), 503

    dados = request.json
    novo_nome = dados.get('nome')

    # 1. Validação
    if not novo_nome or not novo_nome.strip():
        return jsonify({"erro": "O campo 'nome' é obrigatório e não pode ser vazio."}), 400
    
    aluno_ref = db_client.collection('alunos').document(aluno_id)

    try:
        # 2. Verifica se o aluno existe
        if not aluno_ref.get().exists:
            return jsonify({"erro": "Aluno não encontrado."}), 404

        # 3. Atualiza o nome no Firestore
        aluno_ref.update({'nome': novo_nome})

        return jsonify({"mensagem": f"Nome do aluno {aluno_id} alterado para '{novo_nome}' com sucesso."}), 200
        
    except Exception as e:
        print(f"ERRO CRÍTICO DB: {e}")
        return jsonify({"erro": f"Erro ao atualizar nome do aluno: {e}"}), 500