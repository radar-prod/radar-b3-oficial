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
        return ticker  # Futuros não usam .SA
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
            st.error(f"❌ Nenhum dado encontrado para `{ticker}`. Verifique o nome do ativo.")
            st.stop()

        # Resetar índice para transformar o índice em coluna
        data_reset = data.reset_index()

        # 🔥 CORREÇÃO: Remover MultiIndex das colunas (caso o Yahoo retorne MultiIndex)
        if isinstance(data_reset.columns, pd.MultiIndex):
            # Pegar apenas o primeiro nível (nome da coluna)
            new_columns = []
            for col in data_reset.columns:
                if isinstance(col, tuple):
                    # Usa o primeiro nível, ou o segundo se o primeiro for vazio
                    name = col[0] if col[0] else col[1]
                else:
                    name = col
                new_columns.append(name)
            data_reset.columns = new_columns

        # Garantir que temos uma coluna de data
        datetime_col = None
        for col in data_reset.columns:
            if 'datetime' in str(col).lower() or 'date' in str(col).lower():
                datetime_col = col
                break

        if datetime_col is None:
            st.error("❌ Erro: nenhuma coluna de data encontrada (Datetime, Date, etc).")
            st.stop()

        # Renomear para 'Data'
        if datetime_col != 'Data':
            data_reset.rename(columns={datetime_col: 'Data'}, inplace=True)

        # Renomear colunas para o padrão esperado
        rename_map = {}
        for c in data_reset.columns:
            lc = str(c).lower()
            if 'open' in lc or 'abert' in lc: rename_map[c] = 'Abertura'
            if 'high' in lc or 'max' in lc: rename_map[c] = 'Máxima'
            if 'low' in lc or 'min' in lc: rename_map[c] = 'Mínima'
            if 'close' in lc or 'fech' in lc: rename_map[c] = 'Fechamento'
            if 'volume' in lc or lc == 'vol': rename_map[c] = 'Volume'
        data_reset.rename(columns=rename_map, inplace=True)

        # Verificar colunas essenciais
        colunas_necessarias = ['Data', 'Abertura', 'Máxima', 'Mínima', 'Fechamento', 'Volume']
        for col in colunas_necessarias:
            if col not in data_reset.columns:
                st.error(f"❌ Coluna obrigatória ausente: `{col}`")
                st.stop()

        # Converter para datetime
        data_reset['Data'] = pd.to_datetime(data_reset['Data'], errors='coerce', dayfirst=True)
        data_reset = data_reset.dropna(subset=['Data']).copy()
        if data_reset.empty:
            st.error("❌ Dados vazios após conversão da data.")
            st.stop()

        # Criar FakeFile para simular upload
        class FakeFile:
            def __init__(self, name, df):
                self.name = name
                self.df = df

        fake_file = FakeFile(f"{nome_exibicao}.xlsx", data_reset)
        uploaded_files = [fake_file]

        st.success(f"✅ Dados carregados! Total: {len(data_reset)} candles")
        st.write("Colunas finais:", list(data_reset.columns))
        st.dataframe(data_reset.head())

        # Simular função carregar_arquivo do sistema principal
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

                # Normalizar colunas
                df.columns = [str(col).strip().capitalize() for col in df.columns]
                df.rename(columns={
                    'Data': 'data',
                    'Abertura': 'open',
                    'Máxima': 'high',
                    'Mínima': 'low',
                    'Fechamento': 'close',
                    'Volume': 'volume'
                }, inplace=True)

                # Converter data
                df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
                df = df.dropna(subset=['data'])
                df['data_limpa'] = df['data'].dt.floor('min')
                df = df.set_index('data_limpa').sort_index()
                df = df[~df.index.duplicated(keep='first')]

                if df.index.tz:
                    df = df.tz_localize(None)

                st.success(f"✅ {file.name} carregado com sucesso!")
                return df

            except Exception as e:
                st.error(f"❌ Erro ao processar {getattr(file, 'name', 'arquivo')}: {e}")
                return None

        # Testar com cada arquivo
        for file in uploaded_files:
            df_temp = carregar_arquivo(file)
            if df_temp is not None:
                st.write(f"✅ Sucesso! Período: de {df_temp.index.min()} até {df_temp.index.max()}")
                st.dataframe(df_temp[['open', 'high', 'low', 'close']].head())

    except Exception as e:
        st.error(f"❌ Erro geral ao baixar ou processar dados: {e}")
