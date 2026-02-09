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
    # Usando a versão estável do Flash
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Erro de configuração da API: {e}")

# --- INICIALIZAÇÃO DA MEMÓRIA (SESSION STATE) ---
if 'provas_db' not in st.session_state: st.session_state.provas_db = {}
if 'respostas_db' not in st.session_state: st.session_state.respostas_db = []
if 'id_ativa' not in st.session_state: st.session_state.id_ativa = None

# Captura dados da URL
query_params = st.query_params
view = query_params.get("view", "professor")
id_url = query_params.get("prova", "")

# --- FUNÇÃO GERADORA (ROBUSTA) ---
def gerar_questoes_ia(habilidades, materia, num_q):
    prompt = f"""
    Crie {num_q} questões de múltipla escolha para ensino fundamental/médio.
    Disciplina: {materia}
    Foco nas Habilidades: {habilidades}
    
    REGRA DE FORMATAÇÃO (Siga estritamente):
    Para cada questão, escreva uma linha no formato:
    Q|Enunciado da Questão|Alternativa A|Alternativa B|Alternativa C|Alternativa D|Alternativa E|LetraCorreta
    
    Exemplo:
    Q|Quanto é 2+2?|1|2|3|4|5|D
    """
    try:
        # Tenta gerar com a IA
        response = model.generate_content(prompt)
        linhas = [l.strip() for l in response.text.split('\n') if l.startswith('Q|')]
        
        questoes = []
        for linha in linhas:
            partes = linha.split('|')
            if len(partes) >= 8:
                questoes.append({
                    "id": len(questoes) + 1,
                    "habilidade": habilidades,
                    "pergunta": partes[1],
                    "A": partes[2], "B": partes[3], "C": partes[4], "D": partes[5], "E": partes[6],
                    "correta": partes[7].strip().upper()[0] # Garante pegar só a letra
                })
        
        # Se a IA devolveu lista vazia, levanta erro para ir pro "Plano B"
        if not questoes: raise ValueError("IA retornou formato inválido")
        return questoes

    except Exception as e:
        st.warning(f"A IA não pôde gerar automaticamente agora ({e}). Criando modelo manual.")
        # PLANO B: Retorna campos vazios para preenchimento manual
        return [{
            "id": i+1, "habilidade": habilidades, "pergunta": "Digite o enunciado aqui...", 
            "A": "", "B": "", "C": "", "D": "", "E": "", "correta": "A"
        } for i in range(num_q)]

# --- TELA DO ALUNO ---
if view == "aluno":
    if id_url in st.session_state.provas_db:
        prova = st.session_state.provas_db[id_url]
        st.title(f"📝 {prova['materia']} - {prova['turma']}")
        st.subheader(f"Prof. {prova['prof']}")
        
        with st.form("form_aluno"):
            nome_aluno = st.text_input("Nome Completo do Aluno")
            respostas_aluno = {}
            
            for q in prova['questoes']:
                st.write("---")
                st.write(f"**{q['id']}.** {q['pergunta']}")
                # Usa key única baseada na prova e questão
                respostas_aluno[f"q_{q['id']}"] = st.radio(
                    f"Opções da questão {q['id']}", 
                    [f"A) {q['A']}", f"B) {q['B']}", f"C) {q['C']}", f"D) {q['D']}", f"E) {q['E']}"], 
                    key=f"radio_{id_url}_{q['id']}", 
                    label_visibility="collapsed"
                )
            
            if st.form_submit_button("Enviar Avaliação"):
                if nome_aluno:
                    # Salva apenas a letra (primeiro caractere da opção escolhida)
                    dados_limpos = {k: v[0] for k, v in respostas_aluno.items()}
                    st.session_state.respostas_db.append({
                        "ID_Prova": id_url, 
                        "Nome": nome_aluno, 
                        **dados_limpos
                    })
                    st.success("✅ Prova enviada com sucesso!")
                    st.balloons()
                else:
                    st.error("⚠️ Por favor, preencha seu nome.")
    else:
        st.error("🚫 Prova não encontrada. Verifique se o link está correto ou se a prova foi gerada nesta sessão.")

# --- TELA DO PROFESSOR ---
else:
    st.title("🏫 Escola José Carlos Antunes")
    st.caption("Sistema de Gestão de Avaliações | Desenvolvido por Elenir")
    
    aba_criar, aba_relatorio = st.tabs(["📝 Criar Prova", "📊 Relatórios Oficiais"])
    
    with aba_criar:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            prof = c1.text_input("Nome do Professor(a)")
            materia = c1.text_input("Disciplina")
            turma = c2.text_input("Turma (Ex: 9A)")
            habilidades = c2.text_area("Habilidades BNCC")
            num_q = st.slider("Quantidade de Questões", 1, 15, 5)
            
            if st.button("✨ GERAR PROVA COM IA"):
                with st.spinner("Conectando ao Gemini para criar questões..."):
                    # Gera ID único para a prova
                    id_p = f"{materia}_{turma}_{datetime.datetime.now().strftime('%H%M%S')}".replace(" ", "_")
                    
                    # Chama a função (se der erro na IA, traz vazias)
                    questoes_geradas = gerar_questoes_ia(habilidades, materia, num_q)
                    
                    # Salva no banco de dados temporário
                    st.session_state.provas_db[id_p] = {
                        "prof": prof, "materia": materia, "turma": turma, "questoes": questoes_geradas
                    }
                    st.session_state.id_ativa = id_p
                    st.rerun() # Atualiza a tela para mostrar a edição

        # Área de Edição (Só aparece se tiver prova ativa)
        if st.session_state.id_ativa:
            id_atual = st.session_state.id_ativa
            p = st.session_state.provas_db[id_atual]
            
            st.divider()
            st.info(f"🔗 **Link para Alunos:** `https://diagnostica-antunes-2026.streamlit.app/?view=aluno&prova={id_atual}`")
            st.warning("⚠️ Nota: Como ainda não conectamos ao Google Sheets, este link só funcionará enquanto esta aba do navegador estiver aberta.")

            st.subheader("✏️ Revisão das Questões")
            for i, q in enumerate(p['questoes']):
                with st.expander(f"Questão {q['id']}", expanded=False):
                    q['pergunta'] = st.text_area("Enunciado", q['pergunta'], key=f"p_{id_atual}_{i}")
                    cols = st.columns(5)
                    q['A'] = cols[0].text_input("A", q['A'], key=f"a_{id_atual}_{i}")
                    q['B'] = cols[1].text_input("B", q['B'], key=f"b_{id_atual}_{i}")
                    q['C'] = cols[2].text_input("C", q['C'], key=f"c_{id_atual}_{i}")
                    q['D'] = cols[3].text_input("D", q['D'], key=f"d_{id_atual}_{i}")
                    q['E'] = cols[4].text_input("E", q['E'], key=f"e_{id_atual}_{i}")
                    
                    opcoes_validas = ["A", "B", "C", "D", "E"]
                    index_padrao = 0
                    if q['correta'] in opcoes_validas:
                        index_padrao = opcoes_validas.index(q['correta'])
                    
                    q['correta'] = st.selectbox("Gabarito", opcoes_validas, index=index_padrao, key=f"gab_{id_atual}_{i}")

    with aba_relatorio:
        # Seletor de provas
        opcoes_provas = [""] + list(st.session_state.provas_db.keys())
        escolha = st.selectbox("Selecione a Prova para Tabular", opcoes_provas)
        
        if escolha:
            dados_p = st.session_state.provas_db[escolha]
            # Filtra respostas desta prova específica
            respostas_filtradas = [r for r in st.session_state.respostas_db if r['ID_Prova'] == escolha]
            
            if not respostas_filtradas:
                st.info("Aguardando respostas dos alunos para gerar a tabela...")
            else:
                gabarito = [q['correta'] for q in dados_p['questoes']]
                n_q = len(gabarito)
                
                # --- MONTAGEM DO EXCEL OFICIAL (Cabeçalho de 6 linhas) ---
                # Linha 1
                h1 = [" I - Avaliação Diagnóstica", dados_p['materia']] + [""]*(n_q-1) + ["Data"]
                # Linha 2
                h2 = [""]*(n_q+1) + [datetime.date.today().strftime('%d/%m/%Y')]
                # Linha 3
                h3 = ["II - Questões"] + list(range(1, n_q + 1)) + ["Nº de Alunos"]
                # Linha 4
                h4 = ["III - Alternativa Correta"] + gabarito + [len(respostas_filtradas)]
                # Linha 5
                h5 = ["IV -Conhecimento Prévio"] + [""]*(n_q+1)
                # Linha 6 (Cabeçalho da Tabela)
                h6 = ["V - Nome dos(as) estudantes", "VI - Respostas dos(as) estudantes"] + [""]*(n_q-1) + ["Acertos individuais"]
                
                rows = [h1, h2, h3, h4, h5, h6]
                
                # Preenchimento dos Alunos
                for r in respostas_filtradas:
                    # Lista de respostas do aluno (A, B, C...)
                    resps_aluno = [r.get(f"q_{k+1}", "-") for k in range(n_q)]
                    # Cálculo de acertos
                    acertos = sum(1 for k in range(n_q) if resps_aluno[k] == gabarito[k])
                    
                    rows.append([r['Nome']] + resps_aluno + [acertos])
                
                # Criação do DataFrame e Excel
                df_final = pd.DataFrame(rows)
                st.dataframe(df_final) # Mostra prévia na tela
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False, header=False)
                
                st.download_button(
                    label="📥 Baixar Excel Tabulado (Oficial)",
                    data=output.getvalue(),
                    file_name=f"Tabulacao_{escolha}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
