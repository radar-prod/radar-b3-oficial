# teste_isolado.py
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.title("🔧 Teste Isolado: Yahoo Finance → FakeFile → DataFrame")

# Input do usuário
ticker_input = st.text_input("Digite o ativo (ex: PETR4, WINM24):", value="PETR4").strip()
if not ticker_input:
    st.info("Digite um ativo para continuar.")
    st.stop()

# Ajusta o ticker
def ajustar_ticker(ticker):
    ticker = ticker.upper()
    if ticker.endswith(".SA"):
        return ticker
    if ticker.startswith("WIN") or ticker.startswith("WDO"):
        return ticker
    if len(ticker) >= 4 and ticker[-1].isdigit():
        return ticker + ".SA"
    return ticker

ticker = ajustar_ticker(ticker_input)
nome_exibicao = ticker_input.upper()

# Baixar dados
with st.spinner(f"Baixando dados de `{ticker}`..."):
    try:
        data = yf.download(ticker, period="60d", interval="5m", auto_adjust=True, progress=False)
        if data.empty:
            st.error(f"❌ Nenhum dado encontrado para `{ticker}`.")
            st.stop()

        data_reset = data.reset_index()

        # Renomear coluna de data
        if 'Datetime' in data_reset.columns:
            data_reset.rename(columns={'Datetime': 'Data'}, inplace=True)
        elif 'Date' in data_reset.columns:
            data_reset.rename(columns={'Date': 'Data'}, inplace=True)
        else:
            st.error("❌ Coluna de data não encontrada.")
            st.stop()

        # Renomear colunas
        data_reset.rename(columns={
            'Open': 'Abertura',
            'High': 'Máxima',
            'Low': 'Mínima',
            'Close': 'Fechamento',
            'Volume': 'Volume'
        }, inplace=True)

        # Converter para datetime
        data_reset['Data'] = pd.to_datetime(data_reset['Data'], errors='coerce')
        if data_reset['Data'].isna().all():
            st.error("❌ Falha ao converter a coluna 'Data'.")
            st.stop()

        # Criar FakeFile
        class FakeFile:
            def __init__(self, name, df):
                self.name = name
                self.df = df

        fake_file = FakeFile(f"{nome_exibicao}.xlsx", data_reset)
        uploaded_files = [fake_file]

        st.success(f"✅ Dados carregados! Total: {len(data_reset)} candles")
        st.write("Colunas:", list(data_reset.columns))
        st.write("Primeiras 5 linhas:")
        st.dataframe(data_reset.head())

        # Simular carregar_arquivo
        st.subheader("🔍 Teste da função carregar_arquivo")

        def carregar_arquivo(file):
            try:
                # ✅ Se for FakeFile (com .df)
                if hasattr(file, "df"):
                    st.info(f"📁 Detectado FakeFile: {file.name}")
                    df = file.df.copy()
                else:
                    st.info(f"📊 Lendo arquivo real: {file.name}")
                    df = pd.read_excel(file)

                # Verificar se tem coluna 'Data'
                if 'Data' not in df.columns:
                    st.error(f"❌ Erro: coluna 'Data' não encontrada em {file.name}")
                    return None

                df['data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
                df = df.dropna(subset=['data']).copy()
                st.success(f"✅ {file.name} carregado com sucesso!")
                return df
            except Exception as e:
                st.error(f"❌ Erro ao processar {getattr(file, 'name', 'arquivo')}: {e}")
                return None

        # Testar com cada arquivo
        for file in uploaded_files:
            df_temp = carregar_arquivo(file)
            if df_temp is not None:
                st.write(f"✅ Sucesso! Período: de {df_temp['data'].min()} até {df_temp['data'].max()}")
                st.dataframe(df_temp[['data', 'Abertura', 'Fechamento']].head())

    except Exception as e:
        st.error(f"❌ Erro geral: {e}")
