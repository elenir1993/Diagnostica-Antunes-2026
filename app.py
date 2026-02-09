import streamlit as st
import pandas as pd
from docx import Document
import re
import io

# 1. Configuração da Página (Deve ser a primeira coisa)
st.set_page_config(page_title="Gerador de Diagnóstica", page_icon="📝")

st.title("📊 Sistema de Tabulação Diagnóstica")
st.markdown("Suba os arquivos abaixo para gerar o relatório oficial automaticamente.")

# --- FUNÇÕES DE APOIO ---
def extrair_dados_word(file):
    try:
        doc = Document(file)
        texto = "\n".join([p.text for p in doc.paragraphs])
        
        # Busca tags ignorando maiúsculas/minúsculas
        disc_match = re.search(r"DISCIPLINA:\s*(.*)", texto, re.I)
        turma_match = re.search(r"TURMA:\s*(.*)", texto, re.I)
        gab_match = re.search(r"GABARITO:\s*(.*)", texto, re.I)
        
        if not disc_match or not gab_match:
            return None, None, None
            
        disc = disc_match.group(1).split("Data:")[0].strip()
        turma = turma_match.group(1).split("Data:")[0].strip() if turma_match else "Geral"
        gab_raw = gab_match.group(1)
        gabarito = [x.strip().upper() for x in gab_raw.replace(',', ' ').split()]
        
        return disc, turma, gabarito
    except Exception as e:
        st.error(f"Erro ao ler Word: {e}")
        return None, None, None

# --- INTERFACE ---
col1, col2 = st.columns(2)

with col1:
    word_file = st.file_uploader("1. Arquivo Word da Prova", type=["docx"])

with col2:
    csv_file = st.file_uploader("2. CSV do Google Forms", type=["csv"])

if word_file and csv_file:
    dados_prova = extrair_dados_word(word_file)
    disciplina, turma, gabarito = dados_prova

    if disciplina:
        st.success(f"✅ Prova de {disciplina} ({turma}) identificada!")
        num_q = len(gabarito)
        st.info(f"O sistema detectou {num_q} questões no gabarito.")

        if st.button("🚀 Gerar e Baixar Relatório"):
            try:
                # Lendo CSV
                df = pd.read_csv(csv_file)
                
                # Cabeçalho do modelo oficial
                rows = [
                    [" I - Avaliação Diagnóstica", disciplina] + [""] * (num_q - 1) + ["Data"],
                    [""] * (num_q + 1) + ["2026-02-09"],
                    ["II - Questões"] + list(range(1, num_q + 1)) + ["Nº de Alunos"],
                    ["III - Alternativa Correta"] + gabarito + [len(df)],
                    ["IV -Conhecimento Prévio"] + [""] * (num_q + 1),
                    ["V - Nome dos(as) estudantes", "VI - Respostas dos(as) estudantes"] + [""] * (num_q - 1) + ["Acertos individuais"]
                ]

                for _, aluno in df.iterrows():
                    nome = aluno.iloc[1] # Supondo que a 2ª coluna é o Nome
                    
                    respostas = []
                    for i in range(num_q):
                        try:
                            # Tenta pegar a resposta a partir da 4ª coluna (índice 3)
                            val = str(aluno.iloc[3+i]).strip().upper()[0] if not pd.isna(aluno.iloc[3+i]) else "-"
                        except:
                            val = "-"
                        respostas.append(val)
                        
                    acertos = sum(1 for r, g in zip(respostas, gabarito) if r == g)
                    rows.append([nome] + respostas + [acertos])

                # Criar Excel em memória
                output = io.BytesIO()
                df_final = pd.DataFrame(rows)
                
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False, header=False)
                
                st.download_button(
                    label="⬇️ Clique aqui para Baixar o Excel",
                    data=output.getvalue(),
                    file_name=f"Tabulacao_{disciplina}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Erro ao processar dados: {e}")
    else:
        st.error("❌ Tags não encontradas. Verifique se o Word tem 'DISCIPLINA:' e 'GABARITO:'")
