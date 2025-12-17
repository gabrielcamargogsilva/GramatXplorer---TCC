# 🚀 Plataforma de Gamificação para Língua Portuguesa (Backend API)

> **Status do Projeto:** Concluído / Finalizado para TCC 🎓

Este é o motor (Backend) de uma plataforma educativa gamificada focada no ensino de **Língua Portuguesa**. O sistema utiliza **Inteligência Artificial Generativa (Llama 3 via Groq)** para criar exercícios dinâmicos e personalizados, utilizando o **Firebase Firestore** para gerir o progresso dos alunos em tempo real.

---

### 📑 Tabela de Conteúdos
* [📖 Descrição do Projeto](#-descrição-do-projeto)
* [🚀 Funcionalidades Principais](#-funcionalidades-principais)
* [🛠️ Tecnologias Utilizadas](#️-tecnologias-utilizadas)
* [🏗️ Arquitetura do Sistema](#-arquitetura-do-sistema)
* [⚙️ Como Rodar o Projeto Localmente](#️-como-rodar-o-projeto-localmente)
* [🌌 Mecânica de Gamificação](#-mecânica-de-gamificação)
* [👨‍💻 Autor](#-autor)

---

### 📖 Descrição do Projeto
O projeto foi concebido para transformar o aprendizado de gramática e interpretação em uma jornada espacial. Através de uma API Flask robusta, os alunos enfrentam desafios em diferentes galáxias e planetas, recebendo feedback instantâneo gerado por IA sobre seus erros e acertos.

O projeto divide-se em duas grandes trilhas de aprendizagem:
1. **Via Láctea:** Quizzes interativos sobre Morfologia, Sintaxe e Pragmática.
2. **Andrômeda:** Desafios de correção textual onde o aluno atua como revisor de textos propositalmente incorretos.

---

### 🚀 Funcionalidades Principais

- **🤖 Geração de Conteúdo via IA:** Integração com o modelo `llama-3.1-8b-instant` para criar perguntas inéditas e avaliar correções de textos com linguagem adequada ao ensino médio.
- **🛡️ Sistema de Contingência:** Caso a API de IA falhe, o sistema recupera automaticamente questões de reserva diretamente do banco de dados Firebase.
- **🎮 Gamificação Dinâmica:**
    - Evolução por planetas (Netuno, Urano, Saturno, Júpiter e Terra).
    - Metas de pontuação progressivas e atribuição de estrelas.
- **🔐 Segurança:** Autenticação via **JWT (JSON Web Tokens)** com controle de permissões por cargo (*Admin* e *Usuário*).
- **📊 Gestão de Perfil:** Dashboard com progresso detalhado por tópicos (Morfologia, Sintaxe e Pragmática).
- **🖥️ Painel Administrativo:** Interface para gestão completa de usuários (CRUD).

---

### 🛠️ Tecnologias Utilizadas

- **Linguagem:** [Python](https://www.python.org/)
- **Framework Web:** [Flask](https://flask.palletsprojects.com/)
- **IA Generativa:** [Groq Cloud API (Llama 3)](https://groq.com/)
- **Banco de Dados:** [Firebase Firestore](https://firebase.google.com/) (NoSQL)
- **Segurança:** [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/)
- **Variáveis de Ambiente:** [Python-Dotenv](https://pypi.org/project/python-dotenv/)

---

### 🏗️ Arquitetura do Sistema

A API utiliza a estrutura de **Factory Function** e **Blueprints** para manter a modularidade:

* `app.py`: Centraliza a configuração do app, CORS, JWT e Firebase.
* `api/vialactea.py`: Gerencia os quizzes e a lógica de pontuação da Via Láctea.
* `api/andromeda.py`: Gerencia os desafios de correção textual.
* `api/admin.py`: Rotas administrativas para controle de alunos.
* `api/login.py` & `api/cadastro.py`: Sistema de autenticação e criação de IDs sequenciais.
* `utils/groq_firebase.py`: Funções utilitárias para comunicação com as APIs externas.

---

### ⚙️ Como Rodar o Projeto Localmente

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/gabrielcamargogsilva/seu-repositorio.git](https://github.com/gabrielcamargogsilva/seu-repositorio.git)
   cd seu-repositorio

2. **Configure o ambiente virtual**
    ```bash
   python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    pip install -r requirements.txt

3. **Configure as variáveis de ambiente: Crie um arquivo .env na raiz do projeto:**
    ```bash
   CONFIG_FIREBASE='{"seu_json_do_firebase": "..."}'
    GROQ_API_KEY='sua_chave_da_groq'
    CONFIG_JWT='sua_chave_secreta_jwt'

4. **Inicie o servidor:**
    ```bash
    flask run

---

### 🌌 Mecânica de Gamificação

O progresso é dividido em níveis (Planetas) com metas específicas de pontuação e temas de estudo:

| Nível | Planeta | Meta de Pontos | Tema Foco |
| :---: | :--- | :--- | :--- |
| 1 | Netuno | 990 pts | Sintaxe |
| 2 | Urano | 2000 pts | Morfologia |
| 3 | Saturno | 3500 pts | Pragmática |
| 4 | Júpiter | 5000 pts | Revisão Geral |
| 5 | Terra | 7500 pts | Avançado |

---


### 👨‍💻 Autores

O projeto foi desenvolvido de forma colaborativa pela seguinte equipa:

| 🎓 Função | Nome | 🐙 GitHub | 📧 E-mail |
| :--- | :--- | :--- | :--- |
| **Desenvolvedor Back-End** | **Gabriel Camargo G. Silva** | [![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/gabrielcamargogsilva) | [![Email](https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:gabrielcamargogsilva@gmail.com) |
| **Desenvolvedor Back-End** | **Juliano** | [![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/juliano-amaro) | [![Email](https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:juliano.amaro07@gmail.com) |
| **Desenvolvedor Back-End** | **Nicolas** | [![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Nicolas1xx) | [![Email](https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:nirizalu@gmail.com) |

---


> Projeto desenvolvido como parte integrante do Trabalho de Conclusão de Curso (TCC) focado em inovação tecnológica aplicada à educação.
