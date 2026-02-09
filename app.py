import streamlit as st
import pandas as pd
import io
import datetime

# 1. Configuração de Página
st.set_page_config(page_title="Escola José Carlos Antunes", layout="wide")

# Inicialização Robusta do Banco de Dados Temporário
if 'provas_db' not in st.session_state:
    st.session_state.provas_db = {}
if 'respostas_db' not in st.session_state:
    st.session_state.respostas_db = []
if 'id_prova_ativa' not in st.session_state:
    st.session_state.id_prova_ativa = None

# Controle de Navegação (URL)
query_params = st.query_params
view = query_params.get("view", "professor")
id_da_url = query_params.get("prova", "")

# --- VISÃO DO ALUNO ---
if view == "aluno":
    if id_da_url in st.session_state.provas_db:
        p = st.session_state.provas_db[id_da_url]
        st.title(f"📝 {p['materia']} - {p['turma']}")
        st.subheader(f"Professor(a): {p['prof']}")
        
        with st.form("form_aluno"):
            nome_aluno = st.text_input("Seu Nome Completo")
            respostas_aluno = {}
            
            for q in p['questoes']:
                st.write("---")
                st.write(f"**Questão {q['id']}**")
                st.write(q['pergunta'])
                respostas_aluno[f"q_{q['id']}"] = st.radio(f"Opções Q{q['id']}", 
                    [f"A) {q['A']}", f"B) {q['B']}", f"C) {q['C']}", f"D) {q['D']}", f"E) {q['E']}"], 
                    key=f"radio_{id_da_url}_{q['id']}")
            
            if st.form_submit_button("Enviar Respostas"):
                if nome_aluno:
                    # Salva apenas a letra selecionada
                    limpas = {k: v[0] for k, v in respostas_aluno.items()}
                    st.session_state.respostas_db.append({"ID_Prova": id_da_url, "Nome": nome_aluno, **limpas})
                    st.success("Avaliação enviada com sucesso!")
                    st.balloons()
                else:
                    st.error("Por favor, preencha seu nome.")
    else:
        st.error("⚠️ Link inválido ou prova expirada.")

# --- VISÃO DO PROFESSOR ---
else:
    st.title("🏫 Sistema José Carlos Antunes")
    st.caption("Criado por Elenir")

    aba1, aba2 = st.tabs(["🆕 Criar Prova", "📊 Tabulação"])

    with aba1:
        # Formulário de Criação
        with st.container(border=True):
            c1, c2 = st.columns(2)
            prof = c1.text_input("Professor(a)")
            materia = c1.text_input("Disciplina")
            turma = c2.text_input("Turma (Ex: 9A)")
            habilidades = c2.text_area("Habilidades (separe por vírgula)")
            num_q = st.slider("Número de Questões", 1, 20, 5)
            
            if st.button("🚀 GERAR PROVA AGORA"):
                id_gerado = f"{materia}_{turma}_{datetime.datetime.now().strftime('%H%M')}".replace(" ", "_")
                lista_h = [h.strip() for h in habilidades.split(",")] if habilidades else ["Geral"]
                
                novas_questoes = []
                for i in range(num_q):
                    h_atual = lista_h[i % len(lista_h)]
                    novas_questoes.append({
                        "id": i+1,
                        "habilidade": h_atual,
                        "pergunta": f"Analise a situação referente à habilidade {h_atual} e marque a alternativa correta:",
                        "A": "Texto da alternativa A", "B": "Texto da alternativa B", 
                        "C": "Texto da alternativa C", "D": "Texto da alternativa D", "E": "Texto da alternativa E",
                        "correta": "A"
                    })
                
                st.session_state.provas_db[id_gerado] = {
                    "prof": prof, "materia": materia, "turma": turma, "questoes": novas_questoes
                }
                st.session_state.id_prova_ativa = id_gerado

        # Área de Edição (Só aparece após gerar)
        if st.session_state.id_prova_ativa:
            id_atual = st.session_state.id_prova_ativa
            prova = st.session_state.provas_db[id_atual]
            
            st.divider()
            st.warning(f"🔗 **LINK DO ALUNO:** https://diagnostica-antunes-2026.streamlit.app/?view=aluno&prova={id_atual}")
            
            st.subheader("📝 Edite as Questões Abaixo:")
            for i, q in enumerate(prova['questoes']):
                with st.expander(f"QUESTÃO {q['id']} - Habilidade: {q['habilidade']}", expanded=True):
                    q['pergunta'] = st.text_area("Enunciado:", q['pergunta'], key=f"edit_p_{i}")
                    c1, c2, c3, c4, c5 = st.columns(5)
                    q['A'] = c1.text_input("A", q['A'], key=f"edit_a_{i}")
                    q['B'] = c2.text_input("B", q['B'], key=f"edit_b_{i}")
                    q['C'] = c3.text_input("C", q['C'], key=f"edit_c_{i}")
                    q['D'] = c4.text_input("D", q['D'], key=f"edit_d_{i}")
                    q['E'] = c5.text_input("E", q['E'], key=f"edit_e_{i}")
                    q['correta'] = st.selectbox("Gabarito:", ["A", "B", "C", "D", "E"], key=f"edit_cor_{i}")

            if st.button("✅ SALVAR TODAS AS ALTERAÇÕES"):
                st.success("Prova atualizada e pronta para aplicação!")

    with aba2:
        lista_provas = list(st.session_state.provas_db.keys())
        escolha = st.selectbox("Selecione a prova para baixar a tabulação:", [""] + lista_provas)
        
        if escolha:
            p_dados = st.session_state.provas_db[escolha]
            resps = [r for r in st.session_state.respostas_db if r['ID_Prova'] == escolha]
            
            if not resps:
                st.info("Nenhum aluno respondeu esta prova ainda.")
            else:
                gaba = [q['correta'] for q in p_dados['questoes']]
                n_q = len(gaba)
                
                # Cabeçalho Oficial (Igual ao seu CSV)
                linha1 = [" I - Avaliação Diagnóstica", p_dados['materia']] + [""]*(n_q-1) + ["Data"]
                linha2 = [""]*(n_q+1) + [datetime.date.today().strftime('%d/%m/%Y')]
                linha3 = ["II - Questões"] + list(range(1, n_q + 1)) + ["Nº de Alunos"]
                linha4 = ["III - Alternativa Correta"] + gaba + [len(resps)]
                linha5 = ["IV -Conhecimento Prévio"] + [""]*(n_q+1)
                linha6 = ["V - Nome dos(as) estudantes", "VI - Respostas dos(as) estudantes"] + [""]*(n_q-1) + ["Acertos individuais"]
                
                tabulacao = [linha1, linha2, linha3, linha4, linha5, linha6]
                
                for r in resps:
                    respostas_aluno = [r.get(f"q_{i+1}", "-") for i in range(n_q)]
                    acertos = sum(1 for i in range(n_q) if respostas_aluno[i] == gaba[i])
                    tabulacao.append([r['Nome']] + respostas_aluno + [acertos])
                
                df_final = pd.DataFrame(tabulacao)
                st.dataframe(df_final)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False, header=False)
                
                st.download_button("📥 Baixar Excel Oficial", output.getvalue(), f"Tabulacao_{escolha}.xlsx")
