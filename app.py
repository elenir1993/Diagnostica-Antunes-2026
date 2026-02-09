import streamlit as st
import pandas as pd
import io
import datetime
import google.generativeai as genai

# --- CONFIGURAÇÃO DA IA (GOOGLE GEMINI) ---
# Substitua pela sua chave real gerada em https://aistudio.google.com/app/apikey
API_KEY = "AIzaSyCtARJYX6bWZqXtecUZH4EYFzj-KbREctw"

try:
    genai.configure(api_key=API_KEY)
    # Usamos o modelo 1.5-flash que é rápido e compatível
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Erro na configuração da API: {e}")

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Escola José Carlos Antunes", layout="wide")

# Inicialização de Estados (Memória do App)
if 'provas_db' not in st.session_state:
    st.session_state.provas_db = {}
if 'respostas_db' not in st.session_state:
    st.session_state.respostas_db = []
if 'id_ativa' not in st.session_state:
    st.session_state.id_ativa = None

# Controle de Visão (URL)
query_params = st.query_params
view = query_params.get("view", "professor")
id_prova_url = query_params.get("prova", "")

# --- FUNÇÃO DE GERAÇÃO COM IA ---
def gerar_questoes_ia(habilidades, materia, num_q):
    prompt = f"""
    Gere {num_q} questões de múltipla escolha para a disciplina de {materia}.
    Habilidades BNCC: {habilidades}.
    Siga EXATAMENTE este formato de resposta para cada questão (uma por linha):
    Q|Enunciado|A|B|C|D|E|Gabarito
    Exemplo:
    Q|Quanto é 2+2?|1|2|3|4|5|D
    """
    try:
        response = model.generate_content(prompt)
        linhas = [l.strip() for l in response.text.split('\n') if '|' in l]
        questoes = []
        for linha in linhas:
            p = linha.split('|')
            if len(p) >= 8:
                questoes.append({
                    "id": len(questoes) + 1,
                    "habilidade": habilidades,
                    "pergunta": p[1],
                    "A": p[2], "B": p[3], "C": p[4], "D": p[5], "E": p[6],
                    "correta": p[7].strip().upper()[0]
                })
        return questoes
    except Exception as e:
        st.error(f"Falha na IA: {e}")
        return []

# --- VISÃO DO ALUNO ---
if view == "aluno":
    if id_prova_url in st.session_state.provas_db:
        prova = st.session_state.provas_db[id_prova_url]
        st.title(f"📝 Avaliação: {prova['materia']}")
        st.subheader(f"Prof(a): {prova['prof']} | Turma: {prova['turma']}")
        
        with st.form("form_aluno"):
            nome_aluno = st.text_input("Nome Completo")
            respostas_aluno = {}
            
            for q in prova['questoes']:
                st.write("---")
                st.write(f"**Questão {q['id']}**")
                st.write(q['pergunta'])
                respostas_aluno[f"q_{q['id']}"] = st.radio(f"Opções Q{q['id']}", 
                    [f"A) {q['A']}", f"B) {q['B']}", f"C) {q['C']}", f"D) {q['D']}", f"E) {q['E']}"], 
                    key=f"al_q_{q['id']}", label_visibility="collapsed")
            
            if st.form_submit_button("Finalizar Prova"):
                if nome_aluno:
                    dados_envio = {"ID_Prova": id_prova_url, "Nome": nome_aluno}
                    # Salva apenas a letra (primeiro caractere da opção)
                    for k, v in respostas_aluno.items():
                        dados_envio[k] = v[0]
                    st.session_state.respostas_db.append(dados_envio)
                    st.success("Prova enviada com sucesso!")
                    st.balloons()
                else:
                    st.error("Digite o seu nome antes de enviar.")
    else:
        st.error("⚠️ Prova não encontrada ou link expirado.")

# --- VISÃO DO PROFESSOR ---
else:
    st.title("🏫 Escola José Carlos Antunes")
    st.caption("Desenvolvido por Elenir")
    
    aba1, aba2 = st.tabs(["📝 Criar Prova com IA", "📊 Tabulação Oficial"])
    
    with aba1:
        with st.container(border=True):
            col1, col2 = st.columns(2)
            prof = col1.text_input("Nome do Professor")
            materia = col1.text_input("Matéria")
            turma = col2.text_input("Turma (Ex: 9A)")
            habilidades = col2.text_area("Habilidades BNCC (Vírgula para separar)")
            num_q = st.slider("Quantidade de Questões", 1, 20, 5)
            
            if st.button("✨ GERAR QUESTÕES COM IA"):
                with st.spinner("A IA está criando as questões e alternativas..."):
                    id_p = f"{materia}_{turma}_{datetime.datetime.now().strftime('%H%M')}".replace(" ", "")
                    questoes = gerar_questoes_ia(habilidades, materia, num_q)
                    if questoes:
                        st.session_state.provas_db[id_p] = {
                            "prof": prof, "materia": materia, "turma": turma, "questoes": questoes
                        }
                        st.session_state.id_ativa = id_p
                        st.success("Questões geradas com sucesso!")

        if st.session_state.id_ativa:
            id_atual = st.session_state.id_ativa
            p = st.session_state.provas_db[id_atual]
            st.warning(f"🔗 **Link para os Alunos:** https://diagnostica-antunes-2026.streamlit.app/?view=aluno&prova={id_atual}")
            
            st.subheader("Revisão do Professor")
            for i, q in enumerate(p['questoes']):
                with st.expander(f"Questão {q['id']}", expanded=False):
                    q['pergunta'] = st.text_area("Enunciado", q['pergunta'], key=f"ed_p_{i}")
                    q['A'] = st.text_input("A", q['A'], key=f"ed_a_{i}")
                    q['B'] = st.text_input("B", q['B'], key=f"ed_b_{i}")
                    q['C'] = st.text_input("C", q['C'], key=f"ed_c_{i}")
                    q['D'] = st.text_input("D", q['D'], key=f"ed_d_{i}")
                    q['E'] = st.text_input("E", q['E'], key=f"ed_e_{i}")
                    q['correta'] = st.selectbox("Gabarito", ["A", "B", "C", "D", "E"], index=["A","B","C","D","E"].index(q['correta']), key=f"ed_cor_{i}")

    with aba2:
        escolha = st.selectbox("Selecione a Prova", [""] + list(st.session_state.provas_db.keys()))
        if escolha:
            dados_p = st.session_state.provas_db[escolha]
            resps = [r for r in st.session_state.respostas_db if r['ID_Prova'] == escolha]
            
            if resps:
                gaba = [q['correta'] for q in dados_p['questoes']]
                n_q = len(gaba)
                
                # Cabeçalho no modelo EXATO do Governo (CSV enviado)
                h1 = [" I - Avaliação Diagnóstica", dados_p['materia']] + [""]*(n_q-1) + ["Data"]
                h2 = [""]*(n_q+1) + [datetime.date.today().strftime('%d/%m/%Y')]
                h3 = ["II - Questões"] + list(range(1, n_q + 1)) + ["Nº de Alunos"]
                h4 = ["III - Alternativa Correta"] + gaba + [len(resps)]
                h5 = ["IV -Conhecimento Prévio"] + [""]*(n_q+1)
                h6 = ["V - Nome dos(as) estudantes", "VI - Respostas dos(as) estudantes"] + [""]*(n_q-1) + ["Acertos individuais"]
                
                rows = [h1, h2, h3, h4, h5, h6]
                for r in resps:
                    linha_aluno = [r['Nome']] + [r.get(f"q_{i+1}", "-") for i in range(n_q)]
                    acertos = sum(1 for i in range(n_q) if r.get(f"q_{i+1}") == gaba[i])
                    rows.append(linha_aluno + [acertos])
                
                df_final = pd.DataFrame(rows)
                st.dataframe(df_final)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False, header=False)
                st.download_button("📥 Baixar Excel Oficinal", output.getvalue(), f"Tabulacao_{escolha}.xlsx")
            else:
                st.info("Aguardando respostas dos alunos...")
