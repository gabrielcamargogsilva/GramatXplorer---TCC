# app.py

from flask import Flask
from flask_cors import CORS
import os
import sys
import json
from dotenv import load_dotenv

# IMPORTS PARA JWT
from flask_jwt_extended import JWTManager 
from datetime import timedelta 

# Imports do Firebase
import firebase_admin
from firebase_admin import credentials, firestore


# A função create_app() é a Factory Function que inicializa a aplicação
def create_app():
    load_dotenv()
    app = Flask(__name__)
    CORS(app)

    # =========================================================
    # 0. CONFIGURAÇÃO E INICIALIZAÇÃO DO JWT
    # =========================================================
    # A variável CONFIG_JWT deve estar no seu arquivo .env
    app.config['JWT_SECRET_KEY'] = os.getenv('CONFIG_JWT')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=30)
    # Inicializa o JWT Manager, associando-o ao objeto 'app'
    JWTManager(app) 
    
    # =========================================================
    # 1. INICIALIZAÇÃO DO FIREBASE E FIRESTORE
    # =========================================================
    try:
        firebase_config = os.getenv('CONFIG_FIREBASE')
        if firebase_config:
            FBKEY = json.loads(firebase_config)
            cred = credentials.Certificate(FBKEY)
            
            # Inicializa apenas se não estiver inicializado
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
                
            # Armazena o cliente Firestore na configuração do app
            app.config['DB']= firestore.client()
            print("✅ Conectado ao Firebase com sucesso!")
        else:
            app.config['DB']= None
            print("⚠️ CONFIG_FIREBASE não encontrado no .env. Firebase não conectado.")
    except Exception as e:
        print(f"❌ Erro ao conectar ao Firebase: {e}")
        app.config['DB']= None

    # =========================================================
    # 2. IMPORTAÇÃO E REGISTRO DE BLUEPRINTS
    # =========================================================

    # Importações LOCALMENTE dentro da Factory Function para evitar ciclos
    from api.gerais import gerais_bp
    from api.vialactea import vialactea_bp
    from api.andromeda import andromeda_bp
    from api.admin import admin_bp
    from api.login import login_bp
    from api.cadastro import cadastro_bp
    from api.verificar import verificar_bp
    from api.perfil import perfil_bp

    # Registro das rotas
    app.register_blueprint(gerais_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(cadastro_bp)
    app.register_blueprint(verificar_bp)
    app.register_blueprint(perfil_bp)
    
    # Módulos com Prefixo
    app.register_blueprint(vialactea_bp, url_prefix='/vialactea')
    app.register_blueprint(andromeda_bp, url_prefix='/andromeda')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    print("✅ Blueprints registrados com sucesso.")

    # 🔹 Rota raiz (mantida no app principal)
    @app.route('/')
    def home():
        return "<h1>API está on</h1>"

    return app

# =========================================================
# 3. PONTO DE ENTRADA
# =========================================================

if __name__ == '__main__':
    app = create_app()
    # Execute a aplicação
    app.run(debug=True)