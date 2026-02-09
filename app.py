import streamlit as st
import pandas as pd
import io
import datetime
import google.generativeai as genai

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Escola José Carlos Antunes", layout="wide")

# --- CONFIGURAÇÃO DA IA ---
# ⚠️ IMPORTANTE: Substitua abaixo pela sua chave real!
API_KEY = "AIzaSyCtARJYX6bWZqXtecUZH4EYFzj-KbREctw"

try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Erro de configuração da API: {e}")

# --- MEMÓRIA (SESSION STATE) ---
if 'provas_db' not in st.session_state: st.session_state.provas_db = {}
if 'respostas_db' not in st.session_state: st.session_state.respostas_db = []
if 'id_ativa' not in st.session_state: st.session_state.id_ativa = None

# URL
query_params = st.query_params
view = query_params.get("view", "professor")
id_url = query_params.get("prova", "")

# --- FUNÇÃO GERADORA (COM CORREÇÃO DE FALHAS) ---
def gerar_questoes_ia(habilidades, materia, num_q):
    prompt = f"""
    Crie {num_q} questões de múltipla escolha sobre {materia}.
    Habilidades: {habilidades}
    
    REGRA OBRIGATÓRIA DE SAÍDA:
    Não use negrito (**). Não use Markdown.
    Escreva cada questão em uma única linha usando | para separar.
    
    Formato:
    Enunciado da Questão|Alternativa A|Alternativa B|Alternativa C|Alternativa D|Alternativa E|LetraCorreta
    
    Exemplo:
    Quanto é 2+2?|1|2|3|4|5|D
    """
    try:
        response = model.generate_content(prompt)
        # Debug: Mostra o texto cru para o professor ver se deu erro
        st.session_state['debug_texto_ia'] = response.text
        
        linhas = [l.strip() for l in response.text.split('\n') if len(l) > 10]
        questoes = []
        
        for linha in linhas:
            partes = linha.split('|')
            # Se a IA separou certo (tem 7 ou mais partes)
            if len(partes) >= 7:
                questoes.append({
                    "id": len(questoes) + 1,
                    "habilidade": habilidades,
                    "pergunta": partes[0],
                    "A": partes[1], "B": partes[2], "C": partes[3], "D": partes[4], "E": partes[5],
                    "correta": partes[6].strip().upper()[0] if len(partes) > 6 else "A"
                })
            # Se a IA escreveu o texto mas esqueceu das barras, joga tudo no enunciado
            else:
                questoes.append({
                    "id": len(questoes) + 1,
                    "habilidade": habilidades,
                    "pergunta": linha, # Joga o texto todo aqui para não perder
                    "A": "", "B": "", "C": "", "D": "", "E": "", "correta": "A"
                })
                
        return questoes

    except Exception as e:
        st.error(f"Erro na conexão IA: {e}")
        return []

# --- TELA DO ALUNO ---
if view == "aluno":
    if id_url in st.session_state.provas_db:
        prova = st.session_state.provas_db[id_url]
        st.title(f"📝 {prova['materia']} - {prova['turma']}")
        
        with st.form("form_aluno"):
            nome = st.text_input("Nome Completo")
            resps = {}
            for q in prova['questoes']:
                st.write("---")
                st.write(f"**{q['id']}.** {q['pergunta']}")
                resps[f"q_{q['id']}"] = st.radio(f"Opções {q['id']}", [f"A) {q['A']}", f"B) {q['B']}", f"C) {q['C']}", f"D) {q['D']}", f"E) {q['E']}"], key=f"r_{q['id']}", label_visibility="collapsed")
            
            if st.form_submit_button("Enviar"):
                if nome:
                    st.session_state.respostas_db.append({"ID_Prova": id_url, "Nome": nome, **{k: v[0] for k, v in resps.items()}})
                    st.success("Enviado!")
                else:
                    st.error("Nome obrigatório.")
    else:
        st.error("Prova não encontrada.")

# --- TELA DO PROFESSOR ---
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
            
            if st.button("✨ GERAR COM IA"):
                with st.spinner("A IA está pensando..."):
                    qs = gerar_questoes_ia(habs, materia, num)
                    if qs:
                        id_p = f"{materia}_{turma}_{datetime.datetime.now().strftime('%H%M%S')}"
                        st.session_state.provas_db[id_p] = {"prof": prof, "materia": materia, "turma": turma, "questoes": qs}
                        st.session_state.id_ativa = id_p
                        st.rerun()

        # Debugger para você ver o que a IA mandou se der erro
        if 'debug_texto_ia' in st.session_state:
            with st.expander("🕵️ Ver o que a IA respondeu (Debug)"):
                st.text(st.session_state['debug_texto_ia'])

        if st.session_state.id_ativa:
            id_at = st.session_state.id_ativa
            p = st.session_state.provas_db[id_at]
            st.info(f"Link do Aluno: `https://diagnostica-antunes-2026.streamlit.app/?view=aluno&prova={id_at}`")
            
            for i, q in enumerate(p['questoes']):
                with st.expander(f"Questão {q['id']}", expanded=True):
                    q['pergunta'] = st.text_area("Enunciado", q['pergunta'], key=f"p_{i}")
                    cols = st.columns(5)
                    q['A'] = cols[0].text_input("A", q['A'], key=f"a_{i}")
                    q['B'] = cols[1].text_input("B", q['B'], key=f"b_{i}")
                    q['C'] = cols[2].text_input("C", q['C'], key=f"c_{i}")
                    q['D'] = cols[3].text_input("D", q['D'], key=f"d_{i}")
                    q['E'] = cols[4].text_input("E", q['E'], key=f"e_{i}")
                    q['correta'] = st.selectbox("Gabarito", ["A","B","C","D","E"], index=["A","B","C","D","E"].index(q['correta']) if q['correta'] in ["A","B","C","D","E"] else 0, key=f"g_{i}")

    with aba2:
        sel = st.selectbox("Escolha a prova", [""] + list(st.session_state.provas_db.keys()))
        if sel:
            p_d = st.session_state.provas_db[sel]
            rs = [r for r in st.session_state.respostas_db if r['ID_Prova'] == sel]
            if rs:
                gaba = [q['correta'] for q in p_d['questoes']]
                n = len(gaba)
                # Cabeçalho Oficial
                h = [
                    [" I - Avaliação Diagnóstica", p_d['materia']] + [""]*(n-1) + ["Data"],
                    [""]*(n+1) + [datetime.date.today().strftime('%d/%m/%Y')],
                    ["II - Questões"] + list(range(1, n+1)) + ["Nº de Alunos"],
                    ["III - Alternativa Correta"] + gaba + [len(rs)],
                    ["IV -Conhecimento Prévio"] + [""]*(n+1),
                    ["V - Nome dos(as) estudantes", "VI - Respostas dos(as) estudantes"] + [""]*(n-1) + ["Acertos individuais"]
                ]
                for r in rs:
                    resps = [r.get(f"q_{i+1}","-") for i in range(n)]
                    acertos = sum(1 for i in range(n) if resps[i] == gaba[i])
                    h.append([r['Nome']] + resps + [acertos])
                
                df = pd.DataFrame(h)
                st.dataframe(df)
                
                out = io.BytesIO()
                with pd.ExcelWriter(out, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, header=False)
                st.download_button("📥 Baixar Excel", out.getvalue(), f"Tabulacao_{sel}.xlsx")
            else:
                st.warning("Sem respostas ainda.")
