import streamlit as st
import pandas as pd
import os
from google import genai

# =========================
# CONFIGURAÇÃO DA API
# =========================
API_KEY = st.secrets["GOOGLE_API_KEY"]

client = genai.Client(api_key=API_KEY)

# =========================
# FUNÇÃO IA
# =========================
def gerar_questoes_ia(habilidade, disciplina, num_q):
    prompt = f"""
Você é um professor especialista em avaliação diagnóstica.

Crie {num_q} questões de múltipla escolha de {disciplina},
avaliando a seguinte habilidade:

{habilidade}

REGRAS:
- NÃO use markdown
- NÃO numere
- UMA questão por linha
- Use | como separador

FORMATO:
Enunciado|A|B|C|D|E|LetraCorreta
"""

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
    except Exception as e:
        st.error("Erro ao gerar questões com a IA")
        st.exception(e)
        return []

    texto = response.text or ""
    linhas = [l.strip() for l in texto.split("\n") if "|" in l]

    questoes = []
    for i, linha in enumerate(linhas):
        partes = linha.split("|")
        if len(partes) >= 7:
            questoes.append({
                "Questão": i + 1,
                "Habilidade": habilidade,
                "Enunciado": partes[0],
                "A": partes[1],
                "B": partes[2],
                "C": partes[3],
                "D": partes[4],
                "E": partes[5],
                "Gabarito": partes[6].strip()[0]
            })

    return questoes

# =========================
# INTERFACE
# =========================
st.title("🏫 Escola José Carlos Antunes")
st.subheader("Criar Prova Diagnóstica")

professor = st.text_input("Professor")
disciplina = st.text_input("Disciplina")
turma = st.text_input("Turma")
habilidade = st.text_area("Habilidade")
num_q = st.number_input("Número de questões", min_value=1, max_value=20, value=5)

if st.button("Gerar prova"):
    if not habilidade or not disciplina:
        st.warning("Preencha disciplina e habilidade.")
    else:
        questoes = gerar_questoes_ia(habilidade, disciplina, num_q)

        if questoes:
            df = pd.DataFrame(questoes)
            st.success("Prova gerada com sucesso!")
            st.dataframe(df, use_container_width=True)
            st.download_button(
                "Baixar CSV",
                df.to_csv(index=False).encode("utf-8"),
                "prova_diagnostica.csv",
                "text/csv"
            )
