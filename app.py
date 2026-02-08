# Install missing packages
!pip install streamlit python-docx openpyxl

import streamlit as st
import pandas as pd
from docx import Document
import re
import io

# Configuração da Página
st.set_page_config(page_title="Gerador de Diagnóstica", page_icon="📝")

st.title("📊 Sistema de Tabulação Diagnóstica")
st.markdown("Suba os arquivos abaixo para gerar o relatório oficial automaticamente.")

# --- FUNÇÕES DE APOIO ---
def extrair_dados_word(file):
    doc = Document(file)
    texto = "\n".join([p.text for p in doc.paragraphs])
    try:
        disc = re.search(r"DISCIPLINA:\s*(.*)", texto, re.I).group(1).split("Data:")[0].strip()
        turma = re.search(r"TURMA:\s*(.*)", texto, re.I).group(1).split("Data:")[0].strip()
        gab_raw = re.search(r"GABARITO:\s*(.*)", texto, re.I).group(1)
        gabarito = [x.strip().upper() for x in gab_raw.replace(',', ' ').split()]
        return disc, turma, gabarito
    except:
        return None, None, None

# --- INTERFACE ---
col1, col2 = st.columns(2)

with col1:
    word_file = st.file_uploader("1. Arquivo Word da Prova", type=["docx"])

with col2:
    csv_file = st.file_uploader("2. CSV do Google Forms", type=["csv"])

if word_file and csv_file:
    disciplina, turma, gabarito = extrair_dados_word(word_file)

    if disciplina:
        st.success(f"Prova de {disciplina} ({turma}) identificada!")

        if st.button("🚀 Gerar e Baixar Relatório"):
            df = pd.read_csv(csv_file)
            num_q = len(gabarito)

            # Montagem do Modelo (idêntico ao que você enviou)
            rows = [
                [" I - Avaliação Diagnóstica", disciplina] + [""] * (num_q - 1) + ["Data"],
                [""] * (num_q + 1) + ["2026-02-09"],
                ["II - Questões"] + list(range(1, num_q + 1)) + ["Nº de Alunos"],
                ["III - Alternativa Correta"] + gabarito + [len(df)],
                ["IV -Conhecimento Prévio"] + [""] * (num_q + 1),
                ["V - Nome dos(as) estudantes", "VI - Respostas dos(as) estudantes"] + [""] * (num_q - 1) + ["Acertos individuais"]
            ]

            for _, aluno in df.iterrows():
                nome = aluno.iloc[1]
                respostas = [str(aluno.iloc[3+i]).strip().upper()[0] if not pd.isna(aluno.iloc[3+i]) else "-" for i in range(num_q)]
                acertos = sum(1 for r, g in zip(respostas, gabarito) if r == g)
                rows.append([nome] + respostas + [acertos])

            # Criar Excel em memória para download
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                pd.DataFrame(rows).to_excel(writer, index=False, header=False)

            st.download_button(
                label="⬇️ Baixar Excel Pronto",
                data=output.getvalue(),
                file_name=f"Tabulacao_{disciplina}_{turma}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.error("Não foi possível ler as tags DISCIPLINA ou GABARITO no Word.")
