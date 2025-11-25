from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    jwt_required, 
    get_jwt_identity # Usado para obter o email do usuário
)

perfil_bp = Blueprint('perfil', __name__)

@perfil_bp.route('/perfil', methods=["GET"])
@jwt_required()
def get_perfil_aluno():
    # 1. Obtém o e-mail (identity) do token JWT
    email_aluno = get_jwt_identity()
    
    # Acessa o cliente Firestore
    db = current_app.config.get('DB')
    if not db:
        return jsonify({"erro": "Conexão com o banco de dados indisponível"}), 500

    # 2. Busca o documento completo do aluno no Firestore
    try:
        aluno_ref = db.collection('alunos')
        
        # Busca o documento do aluno pelo email
        busca = aluno_ref.where('email', '==', email_aluno).limit(1)
        
        aluno_doc = next(busca.stream(), None)

        if aluno_doc is None:
             # Isso pode acontecer se o token for válido, mas o aluno tiver sido excluído
             return jsonify({'msgerro': 'Aluno não encontrado no banco de dados.'}), 404

        # 3. Retorna todos os dados do aluno
        aluno_data = aluno_doc.to_dict()
        
        # O Firestore pode retornar objetos de Data/Hora que não são serializáveis para JSON.
        # Se for o caso, você pode precisar de uma função auxiliar para converter datas.
        # No entanto, como você armazena 'datanasc' como string, deve funcionar.
        

        return jsonify(aluno_data), 200
    
    except Exception as e:
        print(f"Erro ao buscar perfil do aluno no Firestore: {e}")
        return jsonify({"erro": "Erro interno ao carregar o perfil."}), 500