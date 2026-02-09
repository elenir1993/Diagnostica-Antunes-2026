import streamlit as st
import pandas as pd
import datetime
import io
import uuid

import google.generativeai as genai

# =========================
# CONFIGURAÇÃO DA PÁGINA
# =========================
st.set_page_config(
    page_title="Escola José Carlos Antunes",
    layout="wide"
)

# =========================
# CONFIGURAÇÃO DA IA (AI STUDIO)
# =========================
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-pro")
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

if "prova_ativa" not in st.session_state:
    st.session_state.prova_ativa = None

# =========================
# QUERY PARAMS
# =========================
query_params = st.query_params
view = query_params.get("view", "professor")
prova_id_url = query_params.get("prova", "")

# =========================
# FUNÇÃO DE GERAÇÃO DA IA
# =========================
def gerar_questoes_ia(habilidade, disciplina, num_q):
    prompt = f"""
Você é um professor especialista em avaliação diagnóstica.

Crie {num_q} questões de múltipla escolha de {disciplina},
avaliando a habilidade da BNCC abaixo:

Habilidade:
{habilidade}

REGRAS:
- NÃO use markdown
- NÃO numere as questões
- UMA questão por linha
- Use | para separar os campos

FORMATO EXATO:
Enunciado|A|B|C|D|E|LetraCorreta

EXEMPLO:
Quanto é 2+2?|1|2|3|4|5|D
"""

    response = model.generate_content(prompt)
    texto = response.text.strip()

    linhas = [l.strip() for l in texto.split("\n") if "|" in l]
    questoes = []

    for linha in linhas:
        partes = linha.split("|")
        if len(partes) >= 7:
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

# =========================
# INTERFACE DO ALUNO
# =========================
if view == "aluno":

    if prova_id_url not in st.session_state.provas_db:
        st.error("Prova não encontrada.")
        st.stop()

    prova = st.session_state.provas_db[prova_id_url]
    st.title(f"📝 {prova['nome']}")

    with st.form("form_aluno"):
        nome = st.text_input("Nome completo")
        respostas = {}

        for q in prova["questoes"]:
            st.markdown("---")
            st.write(f"**{q['id']}. {q['pergunta']}**")

            escolha = st.radio(
                "Escolha:",
                ["A", "B", "C", "D", "E"],
                format_func=lambda x: f"{x}) {q[x]}",
                key=f"resp_{q['id']}",
                label_visibility="collapsed"
            )

            respostas[f"q_{q['id']}"] = escolha

        if st.form_submit_button("Enviar prova"):
            if not nome.strip():
                st.error("Informe seu nome.")
            else:
                st.session_state.respostas_db.append({
                    "ID_Prova": prova_id_url,
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
        col1, col2 = st.columns(2)

        professor = col1.text_input("Professor")
        disciplina = col1.text_input("Disciplina")
        turma = col2.text_input("Turma")
        habilidade = col2.text_area("Habilidade (BNCC)")
        num_q = st.slider("Número de questões", 1, 10, 5)

        if st.button("✨ Gerar prova com IA"):
            with st.spinner("Gerando questões..."):
                questoes = gerar_questoes_ia(habilidade, disciplina, num_q)

                if not questoes:
                    st.error("A IA não retornou questões.")
                    st.stop()

                nome_prova = f"{disciplina} – {turma} – {datetime.date.today().strftime('%d/%m/%Y')}"
                prova_id = str(uuid.uuid4())

                st.session_state.provas_db[prova_id] = {
                    "nome": nome_prova,
                    "professor": professor,
                    "disciplina": disciplina,
                    "turma": turma,
                    "questoes": questoes
                }

                st.session_state.prova_ativa = prova_id
                st.rerun()

        # -------- EDIÇÃO --------
        if st.session_state.prova_ativa:
            pid = st.session_state.prova_ativa
            prova = st.session_state.provas_db[pid]

            st.success("Prova criada com sucesso!")
            st.code(f"?view=aluno&prova={pid}")

            for i, q in enumerate(prova["questoes"]):
                with st.expander(f"Questão {q['id']}", expanded=True):
                    q["pergunta"] = st.text_area("Enunciado", q["pergunta"], key=f"p_{i}")
                    cols = st.columns(5)
                    for letra, col in zip(["A", "B", "C", "D", "E"], cols):
                        q[letra] = col.text_input(letra, q[letra], key=f"{letra}_{i}")
                    q["correta"] = st.selectbox(
                        "Gabarito",
                        ["A", "B", "C", "D", "E"],
                        index=["A","B","C","D","E"].index(q["correta"]),
                        key=f"g_{i}"
                    )

    # -------- TABULAÇÃO OFICIAL --------
    with aba2:
        sel = st.selectbox("Selecione a prova", [""] + list(st.session_state.provas_db.keys()))

        if sel:
            prova = st.session_state.provas_db[sel]
            respostas = [r for r in st.session_state.respostas_db if r["ID_Prova"] == sel]

            if not respostas:
                st.warning("Sem respostas.")
                st.stop()

            questoes = prova["questoes"]
            gabarito = [q["correta"] for q in questoes]
            habilidades = [q["habilidade"] for q in questoes]
            n = len(questoes)

            linhas = []

            # Linha I
            linhas.append([
                "I – Avaliação Diagnóstica",
                f"{prova['disciplina']} – Prof. {prova['professor']} – Turma {prova['turma']}"
            ] + [""] * (n - 1) + ["Data"])

            linhas.append([""] * (n + 1) + [datetime.date.today().strftime("%d/%m/%Y")])

            # Linha II
            linhas.append(["II – Habilidade Avaliada"] + habilidades + [""])

            # Linha III
            linhas.append(["III – Alternativa Correta"] + gabarito + [len(respostas)])

            # Linha IV
            linhas.append(["IV – Conhecimento Prévio"] + [""] * (n + 1))

            # Cabeçalho alunos
            linhas.append(["V – Nome dos(as) estudantes"] + list(range(1, n + 1)) + ["Acertos"])

            for r in respostas:
                acertos = sum(1 for i in range(n) if r.get(f"q_{i+1}") == gabarito[i])
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
                "📥 Baixar Excel Oficial",
                buffer.getvalue(),
                file_name=f"Tabulacao_{prova['nome']}.xlsx"
            )
