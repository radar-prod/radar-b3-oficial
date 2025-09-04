import streamlit as st
import pandas as pd
import traceback

st.title("📤 Teste de Upload Excel (debug)")

uploaded_file = st.file_uploader("Escolha um arquivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    st.success("✅ Arquivo carregado com sucesso!")
    st.write("Nome do arquivo:", uploaded_file.name)
    st.write("Tipo do arquivo:", uploaded_file.type)

    try:
        # Força o engine openpyxl
        df = pd.read_excel(uploaded_file, engine="openpyxl")
        st.write("Primeiras 5 linhas:")
        st.dataframe(df.head())
    except Exception as e:
        st.error("❌ Erro ao ler o Excel:")
        st.code(traceback.format_exc())
else:
    st.info("ℹ️ Nenhum arquivo carregado.")
