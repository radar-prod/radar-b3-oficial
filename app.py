# app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Radar B3", layout="wide")
st.markdown("<h1 style='text-align: center;'>🟢 Radar B3 - Dados em Tempo Real (5min)</h1>", unsafe_allow_html=True)

# Input do usuário
ticker = st.text_input("Ticker da ação (ex: PETR4.SA, VALE3.SA, ITUB4.SA):", value="PETR4.SA").strip().upper()

# Adicionar .SA automaticamente se necessário
if ticker and not ticker.endswith(".SA"):
    if len(ticker) <= 5:  # Ações brasileiras geralmente têm 4 letras + número
        ticker += ".SA"

if st.button("🚀 Atualizar Dados") or ticker:
    with st.spinner(f"Baixando dados de {ticker}... (candles de 5 minutos, últimos 60 dias)"):
        try:
            data = yf.download(ticker, period="60d", interval="5m", auto_adjust=True, progress=False)

            if data.empty:
                st.error(f"❌ Nenhum dado encontrado para `{ticker}`. Verifique o ticker.")
            else:
                st.success(f"✅ Dados carregados com sucesso! Última atualização: {data.index[-1].strftime('%Y-%m-%d %H:%M')}")

                # ✅ Correção: calcular dias únicos corretamente
                datas = data.index.date
                dias_unicos = len(np.unique(datas))
                media_por_dia = len(data) // dias_unicos if dias_unicos > 0 else 0

                # Exibir informações gerais
                st.info(f"""
                **Resumo dos dados:**
                - Período: de {data.index[0].strftime('%d/%m/%Y')} até {data.index[-1].strftime('%d/%m/%Y')}
                - Total de candles: {len(data)}
                - Dias únicos com dados: {dias_unicos}
                - Média diária: ~{media_por_dia} candles/dia
                """)

                # Mostrar últimos candles
                st.subheader("📈 Últimos 5 Candles (5min)")
                st.dataframe(
                    data.tail(5)
                    .reset_index()
                    .rename(columns={"Datetime": "Data"})
                    .style.format({
                        "Open": "{:.2f}",
                        "High": "{:.2f}",
                        "Low": "{:.2f}",
                        "Close": "{:.2f}",
                        "Volume": "{:,.0f}",
                        "Data": lambda x: x.strftime("%Y-%m-%d %H:%M") if hasattr(x, "strftime") else x
                    })
                )

                # Gráfico de fechamento
                st.subheader("📉 Preço de Fechamento (últimos 200 candles)")
                st.line_chart(data["Close"].tail(200))

                # Botão para baixar CSV
                @st.cache_data
                def converter_csv(df):
                    return df.reset_index().to_csv(index=False)

                csv = converter_csv(data)
                st.download_button(
                    label="📥 Baixar dados como CSV",
                    data=csv,
                    file_name=f"{ticker}_candles_5min_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

        except Exception as e:
            st.error(f"🚨 Erro ao baixar dados: {e}")
else:
    st.info("Digite um ticker e clique em 'Atualizar Dados' para começar.")

# Rodapé
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Radar B3 - Sistema Automatizado de Análise Intradiária</p>", unsafe_allow_html=True)
