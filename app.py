import streamlit as st
import pandas as pd
import io
import datetime
import google.generativeai as genai

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Escola José Carlos Antunes", layout="wide")

# --- CONFIGURAÇÃO DA IA ---
# ⚠️ COLOQUE SUA CHAVE AQUI
API_KEY = "AIzaSyCtARJYX6bWZqXtecUZH4EYFzj-KbREctw"

try:
    genai.configure(api_key=API_KEY)
    # MUDANÇA AQUI: Usando o modelo 'gemini-pro' que funciona na v1beta
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    st.error(f"Erro de configuração: {e}")

# --- MEMÓRIA (SESSION STATE) ---
if 'provas_db' not in st.session_state: st.session_state.provas_db = {}
if 'respostas_db' not in st.session_state: st.session_state.respostas_db = []
if 'id_ativa' not in st.session_state: st.session_state.id_ativa = None

# URL
query_params = st.query_params
view = query_params.get("view", "professor")
id_url = query_params.get("prova", "")

# --- FUNÇÃO GERADORA ---
def gerar_questoes_ia(habilidades, materia, num_q):
    prompt = f"""
    Crie {num_q} questões de múltipla escolha sobre {materia}.
    Habilidades: {habilidades}
    
    REGRA DE SAÍDA (IMPORTANTE):
    Escreva cada questão em uma única linha separada por barras (|).
    Não use negrito. Não pule linhas entre as questões.
    
    Formato:
    Enunciado|Alternativa A|Alternativa B|Alternativa C|Alternativa D|Alternativa E|LetraCorreta
    
    Exemplo:
    Quanto é 2+2?|1|2|3|4|5|D
    """
    try:
        response = model.generate_content(prompt)
        # Debug para você ver se a IA respondeu
        st.session_state['debug_ia'] = response.text
        
        linhas = [l.strip() for l in response.text.split('\n') if '|' in l]
        questoes = []
        
        for linha in linhas:
            partes = linha.split('|')
            if len(partes) >= 7:
                questoes.append({
                    "id": len(questoes) + 1,
                    "habilidade": habilidades,
                    "pergunta": partes[0],
                    "A": partes[1], "B": partes[2], "C": partes[3], "D": partes[4], "E": partes[5],
                    "correta": partes[6].strip().upper()[0] if len(partes) > 6 else "A"
                })
        
        # Se a IA respondeu mas não formatou certo, usamos o texto cru
        if not questoes and response.text:
             return [{
                "id": 1, "habilidade": habilidades, "pergunta": "A IA gerou o texto mas fora do formato. Copie do Debug abaixo.", 
                "A": "", "B": "", "C": "", "D": "", "E": "", "correta": "A"
            }]

        return questoes

    except Exception as e:
        st.warning(f"Erro ao conectar com Gemini Pro ({e}). Gerando manual.")
        return []

# --- INTERFACE ALUNO ---
if view == "aluno":
    if id_url in st.session_state.provas_db:
        p = st.session_state.provas_db[id_url]
        st.title(f"📝 {p['materia']} - {p['turma']}")
        
        with st.form("form_aluno"):
            nome = st.text_input("Nome Completo")
            resps = {}
            for q in p['questoes']:
                st.write("---")
                st.write(f"**{q['id']}.** {q['pergunta']}")
                resps[f"q_{q['id']}"] = st.radio(f"R{q['id']}", [f"A) {q['A']}", f"B) {q['B']}", f"C) {q['C']}", f"D) {q['D']}", f"E) {q['E']}"], key=f"r_{q['id']}", label_visibility="collapsed")
            
            if st.form_submit_button("Enviar"):
                if nome:
                    st.session_state.respostas_db.append({"ID_Prova": id_url, "Nome": nome, **{k: v[0] for k, v in resps.items()}})
                    st.success("Sucesso!")
                else:
                    st.error("Nome obrigatório.")
    else:
        st.error("Prova não encontrada.")

# --- INTERFACE PROFESSOR ---
else:
    st.title("🏫 Escola José Carlos Antunes")
    
    aba1, aba2 = st.tabs(["📝 Criar Prova", "📊 Tabulação"])
    
    with aba1:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            prof = c1.text_input("Professor")
            materia = c1.text_input("Disciplina")
            turma = c2.text_input("Turma")
            habs = c2.text_area("Habilidades BNCC")
            num = st.slider("Questões", 1, 10, 5)
            
            if st.button("✨ GERAR (Gemini Pro)"):
                with st.spinner("Gerando..."):
                    qs = gerar_questoes_ia(habs, materia, num)
                    if not qs:
                        # Fallback se falhar
                        qs = [{"id": i+1, "habilidade": habs, "pergunta": "", "A":"", "B":"", "C":"", "D":"", "E":"", "correta":"A"} for i in range(num)]
                    
                    id_p = f"{materia}_{turma}_{datetime.datetime.now().strftime('%H%M%S')}"
                    st.session_state.provas_db[id_p] = {"prof": prof, "materia": materia, "turma": turma, "questoes": qs}
                    st.session_state.id_ativa = id_p
                    st.rerun()

        if 'debug_ia' in st.session_state:
            with st.expander("Ver resposta bruta da IA (Debug)"):
                st.text(st.session_state['debug_ia'])

        if st.session_state.id_ativa:
            id_at = st.session_state.id_ativa
            p = st.session_state.provas_db[id_at]
            st.info(f"Link Aluno: `https://diagnostica-antunes-2026.streamlit.app/?view=aluno&prova={id_at}`")
            
            for i, q in enumerate(p['questoes']):
                with st.expander(f"Q{q['id']}", expanded=True):
                    q['pergunta'] = st.text_area("Enunciado", q['pergunta'], key=f"p_{i}")
                    cols = st.columns(5)
                    q['A'] = cols[0].text_input("A", q['A'], key=f"a_{i}")
                    q['B'] = cols[1].text_input("B", q['B'], key=f"b_{i}")
                    q['C'] = cols[2].text_input("C", q['C'], key=f"c_{i}")
                    q['D'] = cols[3].text_input("D", q['D'], key=f"d_{i}")
                    q['E'] = cols[4].text_input("E", q['E'], key=f"e_{i}")
                    idx = ["A","B","C","D","E"].index(q['correta']) if q['correta'] in ["A","B","C","D","E"] else 0
                    q['correta'] = st.selectbox("Gabarito", ["A","B","C","D","E"], index=idx, key=f"g_{i}")

    with aba2:
        sel = st.selectbox("Prova", [""] + list(st.session_state.provas_db.keys()))
        if sel:
            p_d = st.session_state.provas_db[sel]
            rs = [r for r in st.session_state.respostas_db if r['ID_Prova'] == sel]
            if rs:
                g = [q['correta'] for q in p_d['questoes']]
                n = len(g)
                h = [
                    [" I - Avaliação Diagnóstica", p_d['materia']] + [""]*(n-1) + ["Data"],
                    [""]*(n+1) + [datetime.date.today().strftime('%d/%m/%Y')],
                    ["II - Questões"] + list(range(1, n+1)) + ["Nº de Alunos"],
                    ["III - Alternativa Correta"] + g + [len(rs)],
                    ["IV -Conhecimento Prévio"] + [""]*(n+1),
                    ["V - Nome dos(as) estudantes", "VI - Respostas dos(as) estudantes"] + [""]*(n-1) + ["Acertos individuais"]
                ]
                for r in rs:
                    row = [r['Nome']] + [r.get(f"q_{i+1}","-") for i in range(n)] + [sum(1 for i in range(n) if r.get(f"q_{i+1}") == g[i])]
                    h.append(row)
                
                df = pd.DataFrame(h)
                st.dataframe(df)
                out = io.BytesIO()
                with pd.ExcelWriter(out, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, header=False)
                st.download_button("📥 Excel Oficial", out.getvalue(), f"Tabulacao_{sel}.xlsx")
