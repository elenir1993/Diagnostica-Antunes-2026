import streamlit as st
import pandas as pd
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Escola José Carlos Antunes - Sistema Diagnóstico", layout="wide")

# Inicialização de estados
if 'prova_gerada' not in st.session_state:
    st.session_state.prova_gerada = []
if 'respostas_alunos' not in st.session_state:
    st.session_state.respostas_alunos = []

# --- IDENTIDADE VISUAL ---
st.title("🏫 Escola José Carlos Antunes")
st.subheader("Sistema de Avaliação Diagnóstica Automática")
st.caption("Desenvolvido por: Elenir")

# --- NAVEGAÇÃO ---
aba1, aba2, aba3 = st.tabs(["📝 Área do Professor", "✍️ Portal do Aluno", "📊 Relatório e Tabulação"])

# --- ABA 1: PROFESSOR ---
with aba1:
    st.header("Configuração da Prova")
    
    with st.expander("💡 Instruções para Habilidades", expanded=True):
        st.info("Você pode digitar várias habilidades separadas por vírgula (ex: EF09MA01, EF09MA02). A IA distribuirá as questões entre elas.")

    with st.form("config_prova"):
        col1, col2 = st.columns(2)
        with col1:
            nome_prof = st.text_input("Nome do Professor(a)")
            materia = st.text_input("Disciplina")
        with col2:
            habilidades_input = st.text_area("Habilidades BNCC")
            num_questoes = st.slider("Total de Questões", 1, 20, 5)
        
        btn_gerar = st.form_submit_button("Gerar Questões para Revisão")

    if btn_gerar:
        # Simulação de geração (AQUI ENTRARÁ A IA NO FUTURO)
        lista_habilidades = [h.strip() for h in habilidades_input.split(",")]
        novas_questoes = []
        for i in range(num_questoes):
            h_da_vez = lista_habilidades[i % len(lista_habilidades)]
            novas_questoes.append({
                "id": i+1,
                "habilidade": h_da_vez,
                "pergunta": f"Questão sobre {h_da_vez}: [IA gerará o texto aqui]",
                "opcoes": ["A", "B", "C", "D", "E"],
                "correta": "A",
                "aprovada": False
            })
        st.session_state.prova_gerada = novas_questoes
        st.session_state.dados_prova = {"prof": nome_prof, "materia": materia, "habilidades": habilidades_input}

    # Área de Revisão
    if st.session_state.prova_gerada:
        st.divider()
        st.header("Revisão das Questões")
        for i, q in enumerate(st.session_state.prova_gerada):
            with st.container(border=True):
                st.write(f"**Questão {q['id']}** (Habilidade: {q['habilidade']})")
                st.text_area(f"Enunciado {q['id']}", value=q['pergunta'], key=f"txt_{i}")
                
                col_img, col_rev = st.columns([1, 2])
                with col_img:
                    st.file_uploader(f"Adicionar Imagem à Q{q['id']}", type=["jpg", "png"], key=f"img_{i}")
                with col_rev:
                    st.text_input(f"Solicitar modificação para Q{q['id']}", placeholder="Ex: Deixe o texto mais curto...", key=f"mod_{i}")
                    st.checkbox("Questão OK", key=f"ok_{i}")

# --- ABA 2: ALUNO ---
with aba2:
    st.header("📝 Avaliação Online")
    if not st.session_state.prova_gerada:
        st.warning("Nenhuma prova foi liberada pelo professor ainda.")
    else:
        with st.form("prova_aluno"):
            st.info(f"Disciplina: {st.session_state.dados_prova['materia']}")
            nome_aluno = st.text_input("Nome Completo do Aluno")
            turma_aluno = st.text_input("Turma (Ex: 9º Ano A)")
            
            st.divider()
            respostas_atuais = {}
            for q in st.session_state.prova_gerada:
                st.write(f"**{q['id']}.** {q['pergunta']}")
                respostas_atuais[q['id']] = st.radio(f"Escolha a alternativa da Q{q['id']}", q['opcoes'], key=f"aluno_q{q['id']}", label_visibility="collapsed")
                st.write("")
            
            if st.form_submit_button("Finalizar e Enviar Prova"):
                if nome_aluno and turma_aluno:
                    dados_aluno = {"Aluno": nome_aluno, "Turma": turma_aluno, **respostas_atuais}
                    st.session_state.respostas_alunos.append(dados_aluno)
                    st.success("Respostas enviadas com sucesso!")
                    st.balloons()
                else:
                    st.error("Por favor, preencha seu nome e turma.")

# --- ABA 3: TABULAÇÃO ---
with aba3:
    st.header("📊 Resultado Final")
    if not st.session_state.respostas_alunos:
        st.info("As respostas dos alunos aparecerão aqui conforme forem enviadas.")
    else:
        df = pd.DataFrame(st.session_state.respostas_alunos)
        st.write("Dados Consolidados:")
        st.dataframe(df)
        
        # Aqui geramos o Excel no modelo que você enviou antes
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        st.download_button("📥 Baixar Tabulação Oficial (Governo)", output.getvalue(), f"Tabulacao_{st.session_state.dados_prova['materia']}.xlsx")
