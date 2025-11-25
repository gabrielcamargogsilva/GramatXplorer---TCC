# config_data.py

# 🔹 Estrutura de dados para as trilhas de atividades
trilhas_de_atividades = {
    'via_lactea': {
        'via_lactea_fase_1': {'nome': 'Galáxia Via Láctea', 'tema': 'revisao_geral'},
    },
    'andromeda': {
        'andromeda_fase_1': {'nome': 'Galáxia Andrômeda', 'tema': 'revisao_geral'},
    },
}

# 🔹 Estruturas de metas de pontos por trilha (Via Láctea)
metas_pontuacao_via_lactea = {
    1: {'meta': 990, 'nome': 'Netuno', 'tema': 'sintaxe'},
    2: {'meta': 2000, 'nome': 'Urano', 'tema': 'morfologia'},
    3: {'meta': 3500, 'nome': 'Saturno', 'tema': 'pragmatica'},
    4: {'meta': 5000, 'nome': 'Júpiter', 'tema': 'revisao_geral'},
    5: {'meta': 7500, 'nome': 'Terra', 'tema': 'revisao_geral'},
}

# 🔹 Estruturas de metas de pontos por trilha (Andrômeda)
metas_pontuacao_andromeda = {
    1: {'meta': 990, 'nome': 'Sirius'},
    2: {'meta': 2000, 'nome': 'Betelgeuse'},
    3: {'meta': 3500, 'nome': 'Vega'},
    4: {'meta': 5000, 'nome': 'Proxima Centauri'},
    5: {'meta': 7500, 'nome': 'Kepler-186f'},
}

# 🔹 Temas e Contextos de Dificuldade para geração de perguntas
temas_disponiveis = {
    'sintaxe': 'Sintaxe, com foco em Sujeito e Predicado (tipos, concordância), e Objetos Direto e Indireto (diferenciação, uso da preposição). Inclua exemplos práticos para identificar essas funções.',
    'pragmatica': "Pragmática, abordando principalmente Atos de Fala (diretos/indiretos), Ironia e Humor (como são construídos), Regras de cortesia, Pressuposição, Dêixis e Implicatura (o que se subentende). A questão deve exigir interpretação de contexto.",
    'morfologia': "Morfologia, com foco em Radical, Afixos (prefixos e sufixos), Vogal Temática e Desinências na formação e flexão das palavras. Pergunte sobre a estrutura das palavras ou sua classificação morfológica.",
    'revisao_geral': "Revise os conceitos de sintaxe, morfologia e pragmática, focando na identificação de erros de concordância, regência, crase e pontuação. As questões devem apresentar textos com desvios gramaticais para o aluno corrigir ou identificar o erro."
}

contexto_dificuldade = {
    'facil': "Elabore a pergunta com vocabulário mais simples, com foco em conteúdos básicos e exemplos acessíveis.",
    'medio': "Use nível intermediário de complexidade, com exemplos contextualizados e exigência razoável de análise.",
    'dificil': "Inclua maior profundidade e complexidade na pergunta, exigindo maior domínio das regras gramaticais e interpretação sutil."
}