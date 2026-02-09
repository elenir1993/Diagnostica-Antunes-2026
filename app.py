import streamlit as st
import pandas as pd
from google import genai
from io import BytesIO

# =============================
# CONFIGURAÇÕES INICIAIS
# =============================
st.set_page_config(page_title="Avaliação Diagnóstica", layout="centered")

st.title("🏫 Escola José Carlos Antunes")
st.subheader("Sistema de Prova Diagnóstica com IA")

# =============================
# CLIENTE GEMINI (ESTÁVEL)
# =============================
client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

# =============================
# FUNÇÃO IA – GERA QUESTÕES
# =============================
def gerar_questoes_ia(habilidade, disciplina, num_q):
    prompt = f"""
Você é um professor especialista em avaliação diagnóstica.

Crie {num_q} questões de múltipla escolha de {disciplina},
avaliando a habilidade:

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
            model="models/gemini-1.0-pro",
            contents=prompt
        )
    except Exception as e:
        st.error("Erro ao acessar a IA.")
        st.stop()

    texto = response.text or ""
    linhas = [l.strip() for l in texto.split("\n") if "|" in l]

    questoes = []
    for i, linha in enumerate(linhas):
        partes = linha.split("|")
        if len(partes) >= 7:
            questoes.append({
                "Questão": f"Q{i+1}",
                "Habilidade": habilidade,
                "Enunciado": partes[0],
                "A": partes[1],
                "B": partes[2],
                "C": partes[3],
                "D": partes[4],
                "E": partes[5],
                "Correta": partes[6].strip().upper()[0]
            })

    return questoes


# =============================
# FORMULÁRIO
# =============================
st.header("Criar Prova")

professor = st.text_input("Professor")
disciplina = st.text_input("Disciplina")
turma = st.text_input("Turma")

habilidade = st.text_area("Habilidade avaliada")
num_q = st.number_input("Número de questões", min_value=1, max_value=20, value=5)

if st.button("Gerar Prova"):
    if not all([professor, disciplina, turma, habilidade]):
        st.warning("Preencha todos os campos.")
        st.stop()

    with st.spinner("Gerando questões com IA..."):
        questoes = gerar_questoes_ia(habilidade, disciplina, num_q)

    if not questoes:
        st.error("A IA não retornou questões válidas.")
        st.stop()

    st.success("Prova gerada com sucesso!")

    # =============================
    # DATAFRAME DA PROVA
    # =============================
    df_prova = pd.DataFrame(questoes)

    st.subheader("Prévia da Prova")
    st.dataframe(df_prova[["Questão", "Enunciado", "A", "B", "C", "D", "E"]])

    # =============================
    # TABULAÇÃO (EXCEL)
    # =============================
    st.subheader("Gerar Tabulação")

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Linha 1B – mesclada
        cabecalho = pd.DataFrame({
            "": [
                f"Disciplina: {disciplina}",
                f"Professor: {professor}",
                f"Turma: {turma}"
            ]
        })

        cabecalho.to_excel(writer, sheet_name="Tabulação", index=False, header=False, startrow=0)

        # Linha de habilidades por questão
        habilidades_row = [""] + [q["Habilidade"] for q in questoes]

        df_tab = pd.DataFrame(columns=["Aluno"] + [q["Questão"] for q in questoes])
        df_tab.loc[0] = habilidades_row

        df_tab.to_excel(
            writer,
            sheet_name="Tabulação",
            index=False,
            startrow=4
        )

    output.seek(0)

    nome_arquivo = f"Diagnostica_{disciplina}_{turma}.xlsx"

    st.download_button(
        label="📥 Baixar Tabulação",
        data=output,
        file_name=nome_arquivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
