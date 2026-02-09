import streamlit as st
import pandas as pd
import io

# 1. Configuração e Identidade
st.set_page_config(page_title="Escola José Carlos Antunes - Gestão Diagnóstica", layout="wide")

# Inicialização de estados para não perder dados ao navegar
if 'prova_gerada' not in st.session_state:
    st.session_state.prova_gerada = []
if 'respostas_alunos' not in st.session_state:
    st.session_state.respostas_alunos = []
if 'dados_prova' not in st.session_state:
    st.session_state.dados_prova = {}

# Verificar se o link é para aluno ou professor
query_params = st.query_params
is_aluno = query_params.get("view") == "aluno"

# --- LÓGICA DO PROFESSOR ---
if not is_aluno:
    st.title("🏫 Área do Professor - Escola José Carlos Antunes")
    st.caption("Desenvolvido por: Elenir")
    
    aba_gerar, aba_tabulacao = st.tabs(["📝 Criar Avaliação", "📊 Tabulação Oficial"])

    with aba_gerar:
        with st.form("config_prova"):
            col1, col2 = st.columns(2)
            with col1:
                nome_prof = st.text_input("Nome do Professor(a)")
                materia = st.text_input("Disciplina")
                turma = st.text_input("Turma (ex: 9º Ano A)")
            with col2:
                st.info("💡 Aceita várias habilidades separadas por vírgula.")
                habilidades_input = st.text_area("Habilidades BNCC")
                num_questoes = st.slider("Total de Questões", 1, 20, 5)
            
            if st.form_submit_button("Gerar Questões"):
                # Simulação de Enunciados Reais (Substituir por chamada de API no futuro)
                lista_h = [h.strip() for h in habilidades_input.split(",")]
                novas_q = []
                for i in range(num_questoes):
                    h = lista_h[i % len(lista_h)]
                    novas_q.append({
                        "id": i+1,
                        "habilidade": h,
                        "pergunta": f"Considere a habilidade {h}: Qual o resultado da análise do problema proposto para esta competência?",
                        "A": "Opção correta esperada", "B": "Distrator 1", "C": "Distrator 2", "D": "Distrator 3", "E": "Distrator 4",
                        "correta": "A"
                    })
                st.session_state.prova_gerada = novas_q
                st.session_state.dados_prova = {"prof": nome_prof, "materia": materia, "turma": turma, "habilidades": habilidades_input}

        if st.session_state.prova_gerada:
            st.write("---")
            st.subheader("Revisão e Edição")
            st.info(f"🔗 **Link para enviar aos alunos:** `https://diagnostica-antunes-2026.streamlit.app/?view=aluno` ")
            
            for i, q in enumerate(st.session_state.prova_gerada):
                with st.container(border=True):
                    st.text_input(f"Questão {q['id']} - Enunciado", value=q['pergunta'], key=f"p_{i}")
                    c1, c2, c3, c4, c5 = st.columns(5)
                    q['A'] = c1.text_input("A", value=q['A'], key=f"a_{i}")
                    q['B'] = c2.text_input("B", value=q['B'], key=f"b_{i}")
                    q['C'] = c3.text_input("C", value=q['C'], key=f"c_{i}")
                    q['D'] = c4.text_input("D", value=q['D'], key=f"d_{i}")
                    q['E'] = c5.text_input("E", value=q['E'], key=f"e_{i}")
                    
                    col_obs, col_ok = st.columns([3, 1])
                    col_obs.text_input("Observação/Imagem", placeholder="Solicitar alteração...", key=f"obs_{i}")
                    st.checkbox("Aprovar Questão", key=f"ok_{i}")

    with aba_tabulacao:
        if not st.session_state.respostas_alunos:
            st.info("Aguardando respostas dos alunos...")
        else:
            # Lógica para montar o Excel EXATAMENTE como o modelo do Governo
            respostas = st.session_state.respostas_alunos
            gabarito = [q['correta'] for q in st.session_state.prova_gerada]
            num_q = len(gabarito)
            
            # Montagem das linhas de cabeçalho oficiais
            header = [
                [" I - Avaliação Diagnóstica", st.session_state.dados_prova.get('materia', '')] + [""]*(num_q-1) + ["Data"],
                [""]*(num_q+1) + ["2026-02-09"],
                ["II - Questões"] + list(range(1, num_q + 1)) + ["Nº de Alunos"],
                ["III - Alternativa Correta"] + gabarito + [len(respostas)],
                ["IV -Conhecimento Prévio"] + [""]*(num_q + 1),
                ["V - Nome dos(as) estudantes", "VI - Respostas dos(as) estudantes"] + [""]*(num_q-1) + ["Acertos individuais"]
            ]
            
            corpo_dados = []
            for r in respostas:
                linha = [r['Nome']] + [r[f"q_{i+1}"] for i in range(num_q)]
                acertos = sum(1 for i in range(num_q) if r[f"q_{i+1}"] == gabarito[i])
                linha.append(acertos)
                corpo_dados.append(linha)
            
            df_final = pd.DataFrame(header + corpo_dados)
            
            st.dataframe(df_final)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_final.to_excel(writer, index=False, header=False)
            
            st.download_button("📥 Baixar Tabulação Oficial", output.getvalue(), "tabulacao_governo.xlsx")

# --- LÓGICA DO ALUNO ---
else:
    st.title("📝 Avaliação Online")
    st.subheader(f"Escola José Carlos Antunes")
    
    if not st.session_state.prova_gerada:
        st.error("Nenhuma prova disponível no momento. Solicite o link ao professor.")
    else:
        with st.form("prova_aluno"):
            st.write(f"**Disciplina:** {st.session_state.dados_prova.get('materia')}")
            st.write(f"**Professor(a):** {st.session_state.dados_prova.get('prof')}")
            aluno_nome = st.text_input("Nome Completo")
            
            st.divider()
            resp_aluno = {}
            for q in st.session_state.prova_gerada:
                st.write(f"**{q['id']}. {q['pergunta']}**")
                resp_aluno[f"q_{q['id']}"] = st.radio("Selecione:", ["A", "B", "C", "D", "E"], key=f"resp_{q['id']}", horizontal=True)
                st.write("")
            
            if st.form_submit_button("Enviar Respostas"):
                if aluno_nome:
                    resp_aluno["Nome"] = aluno_nome
                    st.session_state.respostas_alunos.append(resp_aluno)
                    st.success("Avaliação enviada com sucesso!")
                    st.balloons()
                else:
                    st.error("Por favor, preencha seu nome.")
