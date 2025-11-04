# app.py

from flask import Flask
from flask_cors import CORS
import os
import sys
import json
from dotenv import load_dotenv

# Importa as dependências do Firebase, mas não o inicializa ainda.
import firebase_admin
from firebase_admin import credentials, firestore


# A importação dos Blueprints agora é LOCAL, dentro da função create_app!
# Isso quebra o ciclo de importação.

def create_app():
    load_dotenv()
    app = Flask(__name__)
    CORS(app)

    # =========================================================
    # 1. INICIALIZAÇÃO DO FIREBASE (DENTRO DA FUNÇÃO)
    # =========================================================
    try:
        firebase_config = os.getenv('CONFIG_FIREBASE')
        if firebase_config:
            FBKEY = json.loads(firebase_config)
            cred = credentials.Certificate(FBKEY)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            app.config['DB']= firestore.client()
            print("✅ Conectado ao Firebase com sucesso!")
        else:
            app.config['DB']= None
            print("⚠️ CONFIG_FIREBASE não encontrado no .env. Firebase não conectado.")
    except Exception as e:
        print(f"❌ Erro ao conectar ao Firebase: {e}")
        app.config['DB']= None

    # =========================================================
    # 2. IMPORTAÇÃO E REGISTRO DE BLUEPRINTS (DENTRO DA FUNÇÃO)
    # =========================================================
    
    # As importações são feitas AQUI, após 'db' ter sido inicializado!
    from api.gerais import gerais_bp
    from api.vialactea import vialactea_bp
    from api.andromeda import andromeda_bp
    from api.admin import admin_bp

    app.register_blueprint(gerais_bp)
    app.register_blueprint(vialactea_bp, url_prefix='/vialactea')
    app.register_blueprint(andromeda_bp, url_prefix='/andromeda')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # 🔹 Rota raiz (mantida no app principal)
    @app.route('/')
    def home():
        return "<h1>API está on</h1>"
        
    return app

# =========================================================
# 3. PONTO DE ENTRADA (MÍNIMO)
# =========================================================

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)