from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

verificar_bp = Blueprint('verificar', __name__)

@verificar_bp.route('/token_info', methods=['GET'])
@jwt_required()
def token_info():
    """
    Endpoint para verificar o JWT e retornar a identidade (email) do usuário.
    Requer um token JWT válido no cabeçalho Authorization.
    """
    try:
        # get_jwt_identity() obtém o valor que foi passado para create_access_token()
        email = get_jwt_identity()
        return jsonify({
            "status": "ok",
            "identity": email,
            "msg": "Token válido, identidade extraída com sucesso."
        }), 200
    except Exception as e:
        # Se houver qualquer falha no processamento (embora @jwt_required() já cuide disso)
        print(f"Erro ao obter identidade do token: {e}")
        return jsonify({"status": "erro", "msg": "Token inválido, expirado ou erro interno."}), 401