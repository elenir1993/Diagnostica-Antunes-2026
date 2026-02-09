import streamlit as st
import pandas as pd
from docx import Document
import io
import re

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="NAMI - Plataforma Educacional", layout="wide")

# --- ESTILO CUSTOMIZADO (OPCIONAL) ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #4CAF50; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE APOIO ---
def gerar_questoes_ia(habilidade, disciplina, num_questoes):
    # Aqui entrará a chamada da API (OpenAI/Gemini)
    # Por enquanto, simulamos o retorno da IA
    simulacao_ia = []
    for i in range(1, num_questoes + 1):
        simulacao_ia.append({
            "id": i,
            "enunciado": f"Questão sobre {habilidade}: Qual o conceito fundamental de {disciplina} aplicado aqui?",
            "alternativas": ["A) Opção 1", "B) Opção 2", "C) Opção 3", "D) Opção 4", "E) Opção 5"],
            "correta": "A"
        })
    return simulacao_ia

# --- NAVEGAÇÃO ---
menu = ["🏠 Início", "📝 Gerar Prova (Professor)", "✍️ Responder Prova (Aluno)", "📊 Tabulação Oficial"]
escolha = st.sidebar.selectbox("Navegação", menu)

# --- PÁGINA INICIAL ---
if escolha == "🏠 Início":
    st.title("🚀 Bem-vindo à NAMI")
    st.subheader("Inteligência e Automação para Professores")
    st.write("Escolha uma opção no menu lateral para começar.")

# --- MÓDULO DO PROFESSOR: GERAR PROVA ---
elif escolha == "📝 Gerar Prova (Professor)":
    st.title("Gerador de Provas Inteligente")
    
    with st.form("form_geracao"):
        col1, col2 = st.columns(2)
        with col1:
            prof = st.text_input("Nome do Professor")
            disciplina = st.text_input("Disciplina")
        with col2:
            habilidade = st.text_input("Habilidade BNCC (ex: EF09MA01)")
            num_q = st.slider("Quantidade de Questões", 1, 20, 10)
        
        btn_gerar = st.form_submit_button("Gerar Prova com IA")

    if btn_gerar:
        with st.spinner("A IA está elaborando as questões..."):
            questoes = gerar_questoes_ia(habilidade, disciplina, num_q)
            st.session_state['prova_atual'] = questoes
            st.success("Prova gerada com sucesso!")

        for q in questoes:
            st.write(f"**{q['id']}. {q['enunciado']}**")
            for alt in q['alternativas']:
                st.write(alt)
        
        st.info("O link para os alunos foi gerado: `nami-educa.streamlit.app/?prova=ativa` (Simulado)")

# --- MÓDULO DO ALUNO: RESPONDER ---
elif escolha == "✍️ Responder Prova (Aluno)":
    st.title("Avaliação Diagnóstica Online")
    
    nome_aluno = st.text_input("Seu Nome Completo")
    turma_aluno = st.text_input("Sua Turma")

    if 'prova_atual' in st.session_state:
        respostas_aluno = {}
        for q in st.session_state['prova_atual']:
            respostas_aluno[q['id']] = st.radio(f"{q['id']}. {q['enunciado']}", ["A", "B", "C", "D", "E"], key=f"q{q['id']}")

        if st.button("Enviar Respostas"):
            # Aqui salvaríamos em um Banco de Dados ou Google Sheets
            st.balloons()
            st.success("Respostas enviadas! Obrigado, " + nome_aluno)
            # Armazenando temporariamente para o exemplo
            if 'respostas_db' not in st.session_state: st.session_state['respostas_db'] = []
            st.session_state['respostas_db'].append({"Nome": nome_aluno, "Turma": turma_aluno, **respostas_aluno})
    else:
        st.warning("Nenhuma prova ativa no momento.")

# --- MÓDULO DE TABULAÇÃO: GOVERNO ---
elif escolha == "📊 Tabulação Oficial":
    st.title("Relatórios e Tabulação")
    
    if 'respostas_db' in st.session_state:
        df = pd.DataFrame(st.session_state['respostas_db'])
        st.write("Dados Coletados em Tempo Real:")
        st.dataframe(df)

        if st.button("Gerar Excel (Modelo do Governo)"):
            # Aqui rodaria a lógica de formatação que criamos no app anterior
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            
            st.download_button("Baixar Tabulação Oficial", output.getvalue(), "tabulacao_nami.xlsx")
            
        # --- ANÁLISE PEDAGÓGICA ---
        st.subheader("Análise NAMI para o Professor")
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Média da Turma", "7.5")
        with col_b:
            st.error("Questão Crítica: Questão 4 (80% de erro)")
    else:
        st.info("Aguardando respostas de alunos para gerar relatórios.")
