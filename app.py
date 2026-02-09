import streamlit as st
import pandas as pd
import io
import datetime

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================
st.set_page_config(
    page_title="Escola José Carlos Antunes",
    layout="wide"
)

# =====================================================
# CONFIGURAÇÃO DA IA
# =====================================================
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-1.0-pro")
except Exception as e:
    st.error(f"Erro ao configurar IA: {e}")
    st.stop()

# =====================================================
# MEMÓRIA
# =====================================================
if "provas_db" not in st.session_state:
    st.session_state.provas_db = {}

if "respostas_db" not in st.session_state:
    st.session_state.respostas_db = []

# =====================================================
# QUERY PARAMS
# =====================================================
params = st.query_params if hasattr(st, "query_params") else {}
view = params.get("view", "professor")
id_url = params.get("prova", "")

# =====================================================
# GERADOR DE QUESTÕES (ROBUSTO)
# =====================================================
def gerar_questoes_ia(habilidade, materia, num_q):

    prompt = f"""
Crie {num_q} questões de múltipla escolha de {materia}.

Habilidade avaliada:
{habilidade}

FORMATO OBRIGATÓRIO (uma questão por linha):
Enunciado|A|B|C|D|E|LetraCorreta
"""

    response = model.generate_content(
        prompt,
        safety_settings={
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
        }
    )

    texto = response.text.strip()
    st.session_state["debug_ia"] = texto

    questoes = []
    for linha in texto.split("\n"):
        partes = linha.split("|")
        if len(partes) == 7:
            questoes.append({
                "id": len(questoes) + 1,
                "habilidade": habilidade,
                "pergunta": partes[0],
                "A": partes[1],
                "B": partes[2],
                "C": partes[3],
                "D": partes[4],
                "E": partes[5],
                "correta": partes[6].strip().upper()[0]
            })

    return questoes

# =====================================================
# INTERFACE DO ALUNO
# =====================================================
if view == "aluno":

    if id_url not in st.session_state.provas_db:
        st.error("Prova não encontrada.")
        st.stop()

    prova = st.session_state.provas_db[id_url]
    st.title(f"{prova['materia']} – {prova['turma']}")

    with st.form("aluno"):
        nome = st.text_input("Nome completo")
        respostas = {}

        for q in prova["questoes"]:
            st.markdown("---")
            st.write(f"{q['id']}. {q['pergunta']}")
            respostas[f"q_{q['id']}"] = st.radio(
                "",
                ["A", "B", "C", "D", "E"],
                key=f"{id_url}_{q['id']}"
            )

        if st.form_submit_button("Enviar"):
            st.session_state.respostas_db.append({
                "ID": id_url,
                "Nome": nome,
                **respostas
            })
            st.success("Prova enviada!")

# =====================================================
# INTERFACE DO PROFESSOR
# =====================================================
else:
    st.title("🏫 Escola José Carlos Antunes")

    aba1, aba2 = st.tabs(["Criar Prova", "Tabulação"])

    # -------------------------------------------------
    # CRIAR PROVA
    # -------------------------------------------------
    with aba1:
        prof = st.text_input("Professor")
        materia = st.text_input("Disciplina")
        turma = st.text_input("Turma")
        habilidade = st.text_area("Habilidade")
        num_q = st.slider("Número de questões", 1, 10, 5)

        if st.button("Gerar Prova"):
            questoes = gerar_questoes_ia(habilidade, materia, num_q)

            if not questoes:
                st.error("A IA não retornou questões válidas.")
                st.stop()

            data = datetime.date.today().strftime("%Y-%m-%d")
            contador = len(st.session_state.provas_db) + 1
            prova_id = f"{materia}_{turma}_{data}_{contador}"

            st.session_state.provas_db[prova_id] = {
                "prof": prof,
                "materia": materia,
                "turma": turma,
                "questoes": questoes
            }

            st.success(f"Prova criada: {prova_id}")

    # -------------------------------------------------
    # TABULAÇÃO
    # -------------------------------------------------
    with aba2:
        sel = st.selectbox("Selecione a prova", list(st.session_state.provas_db.keys()))

        if sel:
            prova = st.session_state.provas_db[sel]
            respostas = [r for r in st.session_state.respostas_db if r["ID"] == sel]

            linhas = []
            linhas.append(
                ["Disciplina", prova["materia"], "Professor", prova["prof"], "Turma", prova["turma"]]
            )

            habilidades = [q["habilidade"] for q in prova["questoes"]]
            gabarito = [q["correta"] for q in prova["questoes"]]

            linhas.append(["Habilidades"] + habilidades)
            linhas.append(["Gabarito"] + gabarito)
            linhas.append(["Aluno"] + list(range(1, len(gabarito) + 1)) + ["Acertos"])

            for r in respostas:
                acertos = sum(
                    r.get(f"q_{i+1}") == gabarito[i]
                    for i in range(len(gabarito))
                )
                linhas.append(
                    [r["Nome"]]
                    + [r.get(f"q_{i+1}", "-") for i in range(len(gabarito))]
                    + [acertos]
                )

            df = pd.DataFrame(linhas)
            st.dataframe(df)

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, header=False)

            st.download_button(
                "Baixar Excel",
                buffer.getvalue(),
                file_name=f"{sel}.xlsx"
            )
