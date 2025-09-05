import yfinance as yf
import pandas as pd

# Configuração
ticker = "PETR4.SA"  # Você pode trocar por "VALE3.SA", "ITUB4.SA", "AAPL", etc
period = "60d"
interval = "5m"

print(f"📊 Buscando dados de {ticker} com intervalo de {interval} (período: {period})...\n")

# Baixar dados
data = yf.download(ticker, period=period, interval=interval, auto_adjust=True, progress=False)

# Verificar se veio vazio
if data.empty:
    print("❌ Nenhum dado retornado. Possíveis causas:")
    print("   - Ticker incorreto")
    print("   - Problema de conexão")
    print("   - Yahoo Finance não tem dados para esse ativo nesse intervalo")
else:
    # Resetar índice para acessar a data
    data_reset = data.reset_index()

    # Converter coluna Datetime para datetime
    data_reset['Datetime'] = pd.to_datetime(data_reset['Datetime'])

    # Extrair datas mínima e máxima
    primeira_data = data_reset['Datetime'].min()
    ultima_data = data_reset['Datetime'].max()
    total_candles = len(data_reset)

    # Contar dias únicos (com dados)
    data_reset['Data'] = data_reset['Datetime'].dt.date
    dias_com_dados = data_reset['Data'].nunique()

    # Informações detalhadas
    print("✅ Dados obtidos com sucesso!")
    print(f"   Ticker: {ticker}")
    print(f"   Intervalo: {interval}")
    print(f"   Período solicitado: {period}")
    print(f"   Primeiro candle: {primeira_data.strftime('%Y-%m-%d %H:%M')}")
    print(f"   Último candle: {ultima_data.strftime('%Y-%m-%d %H:%M')}")
    print(f"   Total de candles de 5min: {total_candles}")
    print(f"   Número de dias com dados: {dias_com_dados}")
    print(f"   Média de candles por dia: {total_candles / dias_com_dados:.1f}")

    # Mostrar os primeiros e últimos candles
    print("\n📈 Primeiros 3 candles:")
    print(data_reset[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']].head(3))

    print("\n📉 Últimos 3 candles:")
    print(data_reset[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']].tail(3))
