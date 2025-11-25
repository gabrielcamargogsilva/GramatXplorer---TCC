from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token

login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['POST'])
def login():
    # Acessa o cliente Firestore (DB) a partir da configuração do app
    db = current_app.config.get('DB')
    if not db:
        return jsonify({'msgerro': 'Erro! Conexão com o banco de dados indisponível'}), 500
        
    dados = request.get_json()
    email = dados.get('email')
    senha = dados.get('senha')

    if not email or not senha:
        return jsonify({'msgerro': 'Erro! Todos os campos devem ser preenchidos'}), 400
    
    aluno_ref = db.collection('alunos')
    
    # Consulta (query) no Firestore: busca aluno por email e senha
    busca = aluno_ref.where('email', '==', email).where('senha', '==', senha)
    
    # Busca o documento completo para garantir que o campo 'cargo' seja recuperado
    select = busca.stream() 

    aluno_encontrado = None
    for doc in select:
        aluno_encontrado = doc.to_dict()
        break 

    if aluno_encontrado is None:
        return jsonify({'msg': 'Senha ou email inválidos!!'}), 400
    else:
        # 1. Recupera o cargo do aluno do documento do Firestore.
        #    Se o campo 'cargo' não existir, assume 'usuario'.
        #    Este campo será 'admin' se o usuário for administrador.
        cargo_usuario = aluno_encontrado.get('cargo', 'usuario')

        # 2. Cria o token, incluindo o cargo nas claims
        token = create_access_token(
            identity=email,
            # Anexa o cargo ao payload do token JWT, que será lido pela rota admin.
            additional_claims={'cargo': cargo_usuario} 
        )
        
        # 3. Retorna o token e o cargo para o cliente
        return jsonify(token=token, cargo=cargo_usuario), 200