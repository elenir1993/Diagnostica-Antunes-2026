import streamlit as st
import pandas as pd
import io
import datetime
import uuid

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# =========================
# CONFIGURAÇÃO DA PÁGINA
# =========================
st.set_page_config(
    page_title="Escola José Carlos Antunes",
    layout="wide"
)

# =========================
# CONFIGURAÇÃO DA IA (SEGURA)
# =========================
try:
    API_KEY = st.secrets["AIzaSyCtARJYX6bWZqXtecUZH4EYFzj-KbREctw"]
    genai.configure(api_key=API_KEY)

    model = genai.GenerativeModel(
        model_name="models/gemini-1.5-flash"
    )

except Exception as e:
    st.error(f"Erro ao configurar IA: {e}")
    st.stop()

# =========================
# MEMÓRIA DO APP
# =========================
if "provas_db" not in st.session_state:
    st.session_state.provas_db = {}

if "respostas_db" not in st.session_state:
    st.session_state.respostas_db = []

if "id_ativa" not in st.session_state:
    st.session_state.id_ativa = None

# =========================
# QUERY PARAMS (COMPATÍVEL)
# =========================
query_params = (
    st.query_params
    if hasattr(st, "query_params")
    else st.experimental_get_query_params()
)

view = query_params.get("view", "professor")
id_url = query_params.get("prova", "")

# =========================
# FUNÇÃO DE GERAÇÃO DA IA
# =========================
def gerar_questoes_ia(habilidades, materia, num_q):
    prompt = f"""
Você é um gerador de provas escolares.

Crie {num_q} questões de múltipla escolha sobre a disciplina {materia}.

Habilidades avaliadas:
{habilidades}

REGRAS OBRIGATÓRIAS:
- NÃO use markdown
- NÃO numere as questões
- Retorne UMA questão por linha
- Separe os campos usando o caractere |

FORMATO EXATO:
Enunciado|Alternativa A|Alternativa B|Alternativa C|Alternativa D|Alternativa E|LetraCorreta

EXEMPLO:
Quanto é 2+2?|1|2|3|4|5|D
"""

    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    try:
        response = model.generate_content(
            prompt,
            safety_settings=safety_settings
        )

        texto = response.text.strip()
        st.session_state["debug_ia"] = texto

        linhas = [l.strip() for l in texto.split("\n") if len(l.strip()) > 10]
        questoes = []

        for linha in linhas:
            partes = linha.split("|")

            if len(partes) >= 7:
                questoes.append({
                    "id": len(questoes) + 1,
                    "habilidade": habilidades,
                    "pergunta": partes[0],
                    "A": partes[1],
                    "B": partes[2],
                    "C": partes[3],
                    "D": partes[4],
                    "E": partes[5],
                    "correta": partes[6].strip().upper()[0]
                })

        if len(questoes) < num_q:
            st.warning("A IA retornou menos questões do que o solicitado.")

        return questoes

    except Exception as e:
        st.error(f"Erro na geração da IA: {e}")
        return []

# =========================
# INTERFACE DO ALUNO
# =========================
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

            alternativas = {
                "A": q["A"],
                "B": q["B"],
                "C": q["C"],
                "D": q["D"],
                "E": q["E"],
            }

            escolha = st.radio(
                "Selecione uma alternativa:",
                list(alternativas.keys()),
                key=f"aluno_{id_url}_{q['id']}",
                label_visibility="collapsed"
            )

            respostas[f"q_{q['id']}"] = escolha

        enviado = st.form_submit_button("Enviar prova")

        if enviado:
            if not nome.strip():
                st.error("Informe seu nome.")
            else:
                st.session_state.respostas_db.append({
                    "ID_Prova": id_url,
                    "Nome": nome,
                    **respostas
                })
                st.success("Prova enviada com sucesso!")

# =========================
# INTERFACE DO PROFESSOR
# =========================
else:
    st.title("🏫 Escola José Carlos Antunes")

    aba1, aba2 = st.tabs(["📝 Criar Prova", "📊 Tabulação"])

    # -------- CRIAÇÃO DA PROVA --------
    with aba1:
        with st.container(border=True):
            c1, c2 = st.columns(2)

            prof = c1.text_input("Professor")
            materia = c1.text_input("Disciplina")
            turma = c2.text_input("Turma")
            habilidades = c2.text_area("Habilidades (BNCC)")
            num_q = st.slider("Número de questões", 1, 10, 5)

            if st.button("✨ GERAR PROVA"):
                with st.spinner("Gerando questões..."):
                    questoes = gerar_questoes_ia(habilidades, materia, num_q)

                    if not questoes:
                        questoes = [{
                            "id": i + 1,
                            "habilidade": habilidades,
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

        # -------- EDIÇÃO DA PROVA --------
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

    # -------- TABULAÇÃO --------
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

            gabarito = [q["correta"] for q in prova["questoes"]]
            n = len(gabarito)

            linhas = [
                ["Aluno"] + list(range(1, n + 1)) + ["Acertos"]
            ]

            for r in respostas:
                acertos = sum(
                    1 for i in range(n)
                    if r.get(f"q_{i+1}") == gabarito[i]
                )

                linhas.append(
                    [r["Nome"]] +
                    [r.get(f"q_{i+1}", "-") for i in range(n)] +
                    [acertos]
                )

            df = pd.DataFrame(linhas)

            st.dataframe(df)

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, header=False)

            st.download_button(
                "📥 Baixar Excel",
                buffer.getvalue(),
                file_name=f"Tabulacao_{sel}.xlsx"
            )
