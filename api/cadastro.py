from flask import Blueprint, request, jsonify, current_app

cadastro_bp = Blueprint('cadastro', __name__)

@cadastro_bp.route('/cadastro', methods=['POST'])
def cadastro():
    # Acessa o cliente Firestore (DB) a partir da configuração do app
    db = current_app.config.get('DB')
    if not db:
        return jsonify({"erro": "Conexão com o banco de dados indisponível"}), 500

    dados = request.json

    # 1. Validação de campos obrigatórios
    campos_obrigatorios = ['nome', 'email', 'senha', 'data_nasc', 'ia_consentimento']
    for campo in campos_obrigatorios:
        if dados is None or campo not in dados:
            return jsonify({"erro": f"Campo obrigatório faltando: {campo}"}), 400
        
    # 2. Lógica de Contador e Geração de ID (USAR TRANSAÇÃO em produção!)
    try:
        contador_ref = db.collection('controle_id').document('contador')
        
        contador_doc = contador_ref.get().to_dict()
        if not contador_doc or contador_doc.get('id') is None:
            return jsonify({"erro": "Documento de controle de ID inválido."}), 500
            
        ultimo_id = contador_doc.get('id')
        novo_id = int(ultimo_id) + 1
        
        contador_ref.update({'id': novo_id})
        
    except Exception as e:
        print(f"Erro ao acessar ou atualizar o contador de ID: {e}")
        return jsonify({"erro": "Erro interno ao gerar o ID do aluno."}), 500


    # 3. Preparação dos dados padrão do novo aluno
    dados_padrao = {
        "id": novo_id,
        "email": dados['email'],
        "senha": dados['senha'], 
        "nome": dados['nome'],
        "cargo":'usuario',
        "datanasc": dados['data_nasc'],
        "ia_consentimento": dados['ia_consentimento'],
        "correct_answers": 1,
        "total_questions_answered": 1,
        "status": True,
        "processo": {
            "via_lactea": {
                "estrelas_por_fase": {},
                "fase_atual": "via_lactea_fase_1",
                "nivel": 1,
                "pontuacao_total": 0
            }
        },
        "progresso_topicos": [
            {"nome": "morfologia", "porcentagem": 0},
            {"nome": "sintaxe", "porcentagem": 0},
            {"nome": "pragmatica", "porcentagem": 0}
        ]
    }

    # 4. Salvar no Firestore
    try:
        db.collection('alunos').document(str(novo_id)).set(dados_padrao)
        return jsonify({'mensagem':'Sucesso!! Aluno cadastrado!'}), 201
    except Exception as e:
        print(f"Erro ao salvar aluno no Firestore: {e}")
        return jsonify({"erro": "Erro ao salvar dados do aluno."}), 500