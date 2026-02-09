import streamlit as st
import pandas as pd
import io
import datetime
import google.generativeai as genai

# --- CONFIGURAÇÃO DA IA ---
# Substitua pela sua chave real ou use st.secrets para segurança
API_KEY = "gen-lang-client-0643311526" 
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-pro')

st.set_page_config(page_title="Escola José Carlos Antunes", layout="wide")

# Inicialização de Estados
if 'provas_db' not in st.session_state: st.session_state.provas_db = {}
if 'respostas_db' not in st.session_state: st.session_state.respostas_db = []
if 'id_prova_ativa' not in st.session_state: st.session_state.id_prova_ativa = None

# Navegação via URL
query_params = st.query_params
view = query_params.get("view", "professor")
id_url = query_params.get("prova", "")

# --- FUNÇÃO PARA GERAR QUESTÕES COM IA ---
def gerar_questoes_ia(habilidades, materia, num_q):
    prompt = f"""
    Atue como um professor especialista na BNCC. Gere {num_q} questões de múltipla escolha para a disciplina de {materia}.
    Habilidades: {habilidades}.
    Cada questão deve ter:
    1. Enunciado claro.
    2. 5 alternativas (A, B, C, D, E).
    3. Indicação de qual é a correta.
    Retorne no formato: Q1|Enunciado|A|B|C|D|E|Correta
    Use | como separador e não use negrito.
    """
    try:
        response = model.generate_content(prompt)
        linhas = response.text.split('\n')
        questoes = []
        for linha in linhas:
            if '|' in linha:
                partes = linha.split('|')
                if len(partes) >= 8:
                    questoes.append({
                        "id": len(questoes)+1,
                        "habilidade": habilidades,
                        "pergunta": partes[1],
                        "A": partes[2], "B": partes[3], "C": partes[4], "D": partes[5], "E": partes[6],
                        "correta": partes[7].replace(")", "").strip()
                    })
        return questoes
    except Exception as e:
        st.error(f"Erro na IA: {e}")
        return []

# --- VISÃO DO ALUNO ---
if view == "aluno":
    if id_url in st.session_state.provas_db:
        p = st.session_state.provas_db[id_url]
        st.title(f"📝 Prova: {p['materia']}")
        st.subheader(f"Prof. {p['prof']} | Turma {p['turma']}")
        
        with st.form("aluno_form"):
            nome = st.text_input("Nome Completo")
            resps = {}
            for q in p['questoes']:
                st.write(f"**{q['id']}.** {q['pergunta']}")
                resps[f"q_{q['id']}"] = st.radio(f"Opções Q{q['id']}", 
                    [f"A) {q['A']}", f"B) {q['B']}", f"C) {q['C']}", f"D) {q['D']}", f"E) {q['E']}"], 
                    key=f"r_{q['id']}", label_visibility="collapsed")
            
            if st.form_submit_button("Enviar"):
                if nome:
                    st.session_state.respostas_db.append({"ID_Prova": id_url, "Nome": nome, **{k: v[0] for k, v in resps.items()}})
                    st.success("Enviado!")
                    st.balloons()
    else:
        st.error("Prova não encontrada.")

# --- VISÃO DO PROFESSOR ---
else:
    st.title("🏫 Sistema José Carlos Antunes")
    st.caption("Desenvolvido por Elenir")
    
    aba1, aba2 = st.tabs(["🆕 Gerar Prova com IA", "📊 Tabulação"])
    
    with aba1:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            prof = c1.text_input("Professor(a)")
            materia = c1.text_input("Disciplina")
            turma = c2.text_input("Turma")
            habilidades = c2.text_area("Habilidades BNCC")
            num_q = st.slider("Quantidade", 1, 15, 5)
            
            if st.button("✨ GERAR QUESTÕES COM IA"):
                with st.spinner("A IA está escrevendo as questões..."):
                    id_p = f"{materia}_{turma}_{datetime.datetime.now().strftime('%H%M')}"
                    questoes = gerar_questoes_ia(habilidades, materia, num_q)
                    if questoes:
                        st.session_state.provas_db[id_p] = {"prof": prof, "materia": materia, "turma": turma, "questoes": questoes}
                        st.session_state.id_prova_ativa = id_p
                        st.success("Questões Geradas!")

        if st.session_state.id_prova_ativa:
            id_atual = st.session_state.id_prova_ativa
            p = st.session_state.provas_db[id_atual]
            st.info(f"🔗 Link do Aluno: `https://diagnostica-antunes-2026.streamlit.app/?view=aluno&prova={id_atual}`")
            
            for i, q in enumerate(p['questoes']):
                with st.expander(f"Questão {q['id']}", expanded=True):
                    q['pergunta'] = st.text_area("Enunciado", q['pergunta'], key=f"ed_p_{i}")
                    q['correta'] = st.selectbox("Gabarito", ["A", "B", "C", "D", "E"], index=["A", "B", "C", "D", "E"].index(q['correta']) if q['correta'] in ["A", "B", "C", "D", "E"] else 0, key=f"ed_c_{i}")

    with aba2:
        # Lógica de Excel idêntica ao modelo oficial que você enviou
        selecao = st.selectbox("Escolha a prova", [""] + list(st.session_state.provas_db.keys()))
        if selecao:
            p_dados = st.session_state.provas_db[selecao]
            resps = [r for r in st.session_state.respostas_db if r['ID_Prova'] == selecao]
            
            if resps:
                gaba = [q['correta'] for q in p_dados['questoes']]
                n_q = len(gaba)
                header = [
                    [" I - Avaliação Diagnóstica", p_dados['materia']] + [""]*(n_q-1) + ["Data"],
                    [""]*(n_q+1) + [datetime.date.today().strftime('%d/%m/%Y')],
                    ["II - Questões"] + list(range(1, n_q + 1)) + ["Nº de Alunos"],
                    ["III - Alternativa Correta"] + gaba + [len(resps)],
                    ["IV -Conhecimento Prévio"] + [""]*(n_q+1),
                    ["V - Nome dos(as) estudantes", "VI - Respostas dos(as) estudantes"] + [""]*(n_q-1) + ["Acertos individuais"]
                ]
                corpo = [[r['Nome']] + [r.get(f"q_{i+1}", "-") for i in range(n_q)] + [sum(1 for i in range(n_q) if r.get(f"q_{i+1}") == gaba[i])] for r in resps]
                df_final = pd.DataFrame(header + corpo)
                st.dataframe(df_final)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False, header=False)
                st.download_button("📥 Baixar Excel Oficial", output.getvalue(), f"Tabulacao_{selecao}.xlsx")
