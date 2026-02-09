import streamlit as st
import pandas as pd
import io
import datetime

# 1. Configuração Inicial
st.set_page_config(page_title="Escola José Carlos Antunes", layout="wide")

# Inicialização de Estados
if 'provas_db' not in st.session_state:
    st.session_state.provas_db = {}
if 'respostas_db' not in st.session_state:
    st.session_state.respostas_db = []

# Detectar URL
query_params = st.query_params
view = query_params.get("view", "professor")
id_prova_url = query_params.get("prova", "")

# --- VISÃO DO ALUNO ---
if view == "aluno":
    if id_prova_url in st.session_state.provas_db:
        prova = st.session_state.provas_db[id_prova_url]
        st.title(f"📝 Avaliação: {prova['materia']}")
        st.subheader(f"Professor(a): {prova['prof']} | Turma: {prova['turma']}")
        
        with st.form("form_aluno"):
            nome_aluno = st.text_input("Nome Completo do Aluno")
            respostas_aluno = {}
            
            for q in prova['questoes']:
                st.write("---")
                st.write(f"**Questão {q['id']}**")
                st.write(q['pergunta'])
                respostas_aluno[f"q_{q['id']}"] = st.radio(f"Alternativas Q{q['id']}", 
                    ["A", "B", "C", "D", "E"], key=f"al_q_{q['id']}", label_visibility="collapsed")
            
            if st.form_submit_button("Enviar Avaliação"):
                if nome_aluno:
                    resultado = {"ID_Prova": id_prova_url, "Nome": nome_aluno, **respostas_aluno}
                    st.session_state.respostas_db.append(resultado)
                    st.success("Enviado com sucesso!")
                    st.balloons()
                else:
                    st.error("Por favor, digite seu nome.")
    else:
        st.error("⚠️ Link inválido ou prova não encontrada.")

# --- VISÃO DO PROFESSOR ---
else:
    st.title("🏫 Gestão Escolar - José Carlos Antunes")
    st.caption("Sistema de Automação de Avaliações - Criado por Elenir")
    
    aba1, aba2 = st.tabs(["🆕 Criar Nova Prova", "📊 Relatórios e Tabulação"])
    
    with aba1:
        with st.form("config"):
            c1, c2 = st.columns(2)
            prof = c1.text_input("Professor(a)")
            materia = c1.text_input("Disciplina")
            turma = c2.text_input("Turma (ex: 9A)")
            habilidades = c2.text_area("Habilidades BNCC (separe por vírgula)")
            num_q = c1.slider("Quantidade de Questões", 1, 20, 5)
            if st.form_submit_button("Gerar Base da Prova"):
                id_prova = f"{materia}_{turma}".replace(" ", "_")
                lista_h = [h.strip() for h in habilidades.split(",")]
                questoes_fake = []
                for i in range(num_q):
                    h = lista_h[i % len(lista_h)]
                    questoes_fake.append({
                        "id": i+1, "habilidade": h, 
                        "pergunta": f"Baseado na habilidade {h}, analise e responda...",
                        "A": "Alternativa A", "B": "Alternativa B", "C": "Alternativa C", "D": "Alternativa D", "E": "Alternativa E",
                        "correta": "A"
                    })
                st.session_state.provas_db[id_prova] = {
                    "prof": prof, "materia": materia, "turma": turma, 
                    "habilidades": habilidades, "questoes": questoes_fake
                }
                st.session_state.id_editando = id_prova

        if 'id_editando' in st.session_state:
            id_atual = st.session_state.id_editando
            p = st.session_state.provas_db[id_atual]
            st.divider()
            st.subheader(f"✍️ Editando Prova: {id_atual}")
            
            link_aluno = f"https://diagnostica-antunes-2026.streamlit.app/?view=aluno&prova={id_atual}"
            st.success(f"🔗 **Link Único desta Prova:** {link_aluno}")

            for i, q in enumerate(p['questoes']):
                with st.expander(f"Editar Questão {q['id']} ({q['habilidade']})", expanded=True):
                    q['pergunta'] = st.text_area("Enunciado", q['pergunta'], key=f"p_{id_atual}_{i}")
                    cols = st.columns(5)
                    q['A'] = cols[0].text_input("A", q['A'], key=f"a_{id_atual}_{i}")
                    q['B'] = cols[1].text_input("B", q['B'], key=f"b_{id_atual}_{i}")
                    q['C'] = cols[2].text_input("C", q['C'], key=f"c_{id_atual}_{i}")
                    q['D'] = cols[3].text_input("D", q['D'], key=f"d_{id_atual}_{i}")
                    q['E'] = cols[4].text_input("E", q['E'], key=f"e_{id_atual}_{i}")
                    q['correta'] = st.selectbox("Alternativa Correta", ["A", "B", "C", "D", "E"], key=f"cor_{id_atual}_{i}")
            
            if st.button("💾 Salvar Alterações e Liberar Link"):
                st.toast("Prova salva e pronta para os alunos!")

    with aba2:
        provas_disponiveis = list(st.session_state.provas_db.keys())
        prova_sel = st.selectbox("Selecione a Prova para Gerar Excel", [""] + provas_disponiveis)
        
        if prova_sel:
            dados_prova = st.session_state.provas_db[prova_sel]
            respostas = [r for r in st.session_state.respostas_db if r['ID_Prova'] == prova_sel]
            
            if not respostas:
                st.warning("Ainda não há respostas para esta prova.")
            else:
                gabarito = [q['correta'] for q in dados_prova['questoes']]
                num_q = len(gabarito)
                
                # Montagem do Cabeçalho Oficial
                header = [
                    [" I - Avaliação Diagnóstica", dados_prova['materia']] + [""]*(num_q-1) + ["Data"],
                    [""]*(num_q+1) + [datetime.date.today().strftime('%Y-%m-%d')],
                    ["II - Questões"] + list(range(1, num_q + 1)) + ["Nº de Alunos"],
                    ["III - Alternativa Correta"] + gabarito + [len(respostas)],
                    ["IV -Conhecimento Prévio"] + [""]*(num_q + 1),
                    ["V - Nome dos(as) estudantes", "VI - Respostas dos(as) estudantes"] + [""]*(num_q-1) + ["Acertos individuais"]
                ]
                
                # Dados dos Alunos
                corpo = []
                for r in respostas:
                    linha = [r['Nome']]
                    resp_list = [r.get(f"q_{i+1}", "-") for i in range(num_q)]
                    acertos = sum(1 for i in range(num_q) if resp_list[i] == gabarito[i])
                    corpo.append(linha + resp_list + [acertos])
                
                df_excel = pd.DataFrame(header + corpo)
                st.dataframe(df_excel)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_excel.to_excel(writer, index=False, header=False)
                
                st.download_button("📥 Baixar Tabulação Governo (.xlsx)", output.getvalue(), f"Tabulacao_{prova_sel}.xlsx")
