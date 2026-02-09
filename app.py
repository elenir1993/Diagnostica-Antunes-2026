import streamlit as st
import pandas as pd
import io
import datetime
import uuid
import json

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
# CONFIGURAÇÃO DA IA (SEGURA)
# =====================================================
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)

    model = genai.GenerativeModel(
        model_name="models/gemini-1.5-flash"
    )
except Exception as e:
    st.error(f"Erro ao configurar IA: {e}")
    st.stop()

# =====================================================
# MEMÓRIA DO APP
# =====================================================
if "provas_db" not in st.session_state:
    st.session_state.provas_db = {}

if "respostas_db" not in st.session_state:
    st.session_state.respostas_db = []

if "id_ativa" not in st.session_state:
    st.session_state.id_ativa = None

# =====================================================
# QUERY PARAMS
# =====================================================
query_params = (
    st.query_params
    if hasattr(st, "query_params")
    else st.experimental_get_query_params()
)

view = query_params.get("view", "professor")
id_url = query_params.get("prova", "")

# =====================================================
# FUNÇÃO DE GERAÇÃO DAS QUESTÕES (IA)
# =====================================================
def gerar_questoes_ia(habilidade, materia, num_q):

    prompt = f"""
Você é um professor experiente da rede pública.

Crie exatamente {num_q} questões de múltipla escolha
para uma avaliação diagnóstica da disciplina {materia}.

Habilidade avaliada (texto digitado pelo professor):
"{habilidade}"

REGRAS:
- Linguagem clara
- Adequado ao nível da turma
- Apenas UMA alternativa correta
- Não use markdown
- Não escreva texto fora do JSON

RETORNE APENAS UM JSON VÁLIDO neste formato:

[
  {{
    "enunciado": "texto da questão",
    "alternativas": {{
      "A": "texto",
      "B": "texto",
      "C": "texto",
      "D": "texto",
      "E": "texto"
    }},
    "correta": "A"
  }}
]
"""

    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    try:
        response = model.generate_content(prompt, safety_settings=safety_settings)
        raw = response.text.strip()
        st.session_state["debug_ia"] = raw

        dados = json.loads(raw)

        questoes = []
        for i, q in enumerate(dados):
            questoes.append({
                "id": i + 1,
                "habilidade": habilidade,
                "pergunta": q["enunciado"],
                "A": q["alternativas"]["A"],
                "B": q["alternativas"]["B"],
                "C": q["alternativas"]["C"],
                "D": q["alternativas"]["D"],
                "E": q["alternativas"]["E"],
                "correta": q["correta"]
            })

        return questoes

    except Exception as e:
        st.error("❌ A IA não retornou dados válidos.")
        st.exception(e)
        return []

# =====================================================
# INTERFACE DO ALUNO
# =====================================================
if view == "aluno":

    if id_url not in st.session_state.provas_db:
        st.error("Prova não encontrada.")
        st.stop()

    prova = st.session_state.provas_db[id_url]
    st.title(f"📝 {prova['materia']} — {prova['turma']}")

    with st.form("form_aluno"):
        nome = st.text_input("Nome completo")
        respostas = {}

        for q in prova["questoes"]:
            st.markdown("---")
            st.write(f"**{q['id']}. {q['pergunta']}**")

            escolha = st.radio(
                "Selecione uma alternativa:",
                ["A", "B", "C", "D", "E"],
                key=f"aluno_{id_url}_{q['id']}",
                label_visibility="collapsed"
            )

            respostas[f"q_{q['id']}"] = escolha

        enviado = st.form_submit_button("Enviar prova")

        if enviado:
            if not nome.strip():
                st.error("Informe seu nome.")
            elif len(respostas) < len(prova["questoes"]):
                st.error("Responda todas as questões.")
            else:
                st.session_state.respostas_db.append({
                    "ID_Prova": id_url,
                    "Nome": nome,
                    **respostas
                })
                st.success("Prova enviada com sucesso!")

# =====================================================
# INTERFACE DO PROFESSOR
# =====================================================
else:
    st.title("🏫 Escola José Carlos Antunes")

    aba1, aba2 = st.tabs(["📝 Criar Prova", "📊 Tabulação Oficial"])

    # =================================================
    # CRIAÇÃO DA PROVA
    # =================================================
    with aba1:
        with st.container(border=True):
            c1, c2 = st.columns(2)

            prof = c1.text_input("Professor")
            materia = c1.text_input("Disciplina")
            turma = c2.text_input("Turma")
            habilidade = c2.text_area("Habilidade avaliada (texto livre)")
            num_q = st.slider("Número de questões", 1, 10, 5)

            if st.button("✨ GERAR PROVA"):
                questoes = gerar_questoes_ia(habilidade, materia, num_q)

                if not questoes:
                    questoes = [{
                        "id": i + 1,
                        "habilidade": habilidade,
                        "pergunta": "Digite o enunciado",
                        "A": "", "B": "", "C": "", "D": "", "E": "",
                        "correta": "A"
                    } for i in range(num_q)]

                prova_id = str(uuid.uuid4())

                st.session_state.provas_db[prova_id] = {
                    "prof": prof,
                    "materia": materia,
                    "turma": turma,
                    "questoes": questoes
                }

                st.session_state.id_ativa = prova_id
                st.rerun()

        if "debug_ia" in st.session_state:
            with st.expander("🛠 Texto bruto da IA"):
                st.text(st.session_state["debug_ia"])

        # =================================================
        # EDIÇÃO DA PROVA
        # =================================================
        if st.session_state.id_ativa:
            pid = st.session_state.id_ativa
            prova = st.session_state.provas_db[pid]

            st.info(
                f"Link do aluno:\n"
                f"https://diagnostica-antunes-2026.streamlit.app/?view=aluno&prova={pid}"
            )

            for i, q in enumerate(prova["questoes"]):
                with st.expander(f"Questão {q['id']}", expanded=True):
                    q["pergunta"] = st.text_area(
                        "Enunciado",
                        q["pergunta"],
                        key=f"{pid}_p_{i}"
                    )

                    cols = st.columns(5)
                    for letra, col in zip(["A", "B", "C", "D", "E"], cols):
                        q[letra] = col.text_input(
                            letra,
                            q[letra],
                            key=f"{pid}_{letra}_{i}"
                        )

                    q["correta"] = st.selectbox(
                        "Gabarito",
                        ["A", "B", "C", "D", "E"],
                        index=["A", "B", "C", "D", "E"].index(q["correta"]),
                        key=f"{pid}_g_{i}"
                    )

    # =================================================
    # TABULAÇÃO OFICIAL (MESCLADA)
    # =================================================
    with aba2:
        sel = st.selectbox(
            "Selecione a prova",
            [""] + list(st.session_state.provas_db.keys())
        )

        if sel:
            prova = st.session_state.provas_db[sel]
            respostas = [
                r for r in st.session_state.respostas_db
                if r["ID_Prova"] == sel
            ]

            if not respostas:
                st.warning("Ainda não há respostas.")
                st.stop()

            questoes = prova["questoes"]
            n = len(questoes)

            gabarito = [q["correta"] for q in questoes]
            habilidades_q = [q["habilidade"] for q in questoes]

            linhas = []

            # LINHA I – Cabeçalho institucional
            linhas.append(
                ["I – Avaliação Diagnóstica",
                 f"{prova['materia']} – Prof. {prova['prof']} – Turma {prova['turma']}"]
                + [""] * (n - 1)
                + ["Data"]
            )

            linhas.append(
                [""] * (n + 1) + [datetime.date.today().strftime("%d/%m/%Y")]
            )

            # LINHA II – Habilidades por questão
            linhas.append(
                ["II – Habilidade Avaliada"]
                + habilidades_q
                + [""]
            )

            # LINHA III – Gabarito
            linhas.append(
                ["III – Alternativa Correta"]
                + gabarito
                + [len(respostas)]
            )

            # LINHA IV – Conhecimento Prévio
            linhas.append(
                ["IV – Conhecimento Prévio"]
                + [""] * (n + 1)
            )

            # LINHA V – Cabeçalho alunos
            linhas.append(
                ["V – Nome dos(as) estudantes"]
                + list(range(1, n + 1))
                + ["Acertos"]
            )

            # LINHAS DOS ALUNOS
            for r in respostas:
                acertos = sum(
                    1 for i in range(n)
                    if r.get(f"q_{i+1}") == gabarito[i]
                )

                linhas.append(
                    [r["Nome"]]
                    + [r.get(f"q_{i+1}", "-") for i in range(n)]
                    + [acertos]
                )

            df = pd.DataFrame(linhas)
            st.dataframe(df)

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, header=False)

            st.download_button(
                "📥 Baixar Excel Oficial",
                buffer.getvalue(),
                file_name=f"Tabulacao_{sel}.xlsx"
            )
