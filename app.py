# app.py - Radar B3 (versão com Yahoo Finance integrado)
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, time as time_obj
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========================
# SIMULAÇÃO DE LOGIN
# ========================
if "email" not in st.session_state:
    st.session_state.email = "teste@gmail.com"
    st.session_state.plano = "Diamante"
    st.session_state.expira = datetime.now().date() + pd.Timedelta(days=30)

# ========================
# FUNÇÃO: extrair nome do arquivo
# ========================
def extrair_nome_completo(file_name):
    return file_name.split(".")[0]

# ========================
# FUNÇÃO: identificar tipo do ativo
# ========================
def identificar_tipo(ticker):
    ticker = ticker.upper().strip()
    if '.' in ticker:
        ticker = ticker.split('.')[0]
    prefixos = ['5-MIN_', '5_MIN_', 'MINI_', 'MIN_', 'INTRADAY_', 'INTRADAY']
    for p in prefixos:
        if ticker.startswith(p):
            ticker = ticker[len(p):]
    if 'WIN' in ticker or 'INDICE' in ticker:
        return 'mini_indice'
    if 'WDO' in ticker or 'DOLAR' in ticker or 'DOL' in ticker:
        return 'mini_dolar'
    acoes = ['PETR', 'VALE', 'ITUB', 'BBDC', 'BEEF', 'ABEV', 'ITSA', 'JBSS', 'RADL', 'CIEL',
             'GOLL', 'AZUL', 'BBAS', 'SANB', 'ASAI', 'B3SA', 'MGLU', 'CVCB', 'IRBR', 'XP', 'LCAM']
    for acao in acoes:
        if acao in ticker:
            return 'acoes'
    return 'acoes'

# ========================
# FUNÇÃO: ajustar ticker (PETR4 → PETR4.SA | WINM24 → WINM24)
# ========================
def ajustar_ticker(ticker_input):
    ticker = ticker_input.strip().upper()
    if ticker.endswith(".SA"):
        return ticker
    if ticker.startswith("WIN") or ticker.startswith("WDO"):
        return ticker  # Futuros não usam .SA
    if len(ticker) >= 4 and ticker[-1].isdigit():
        return ticker + ".SA"
    return ticker

# ========================
# FUNÇÃO DE RASTREAMENTO INTRADAY (otimizada)
# ========================
def processar_rastreamento_intraday(
    uploaded_files,
    tipo_ativo,
    qtd,
    candles_pos_entrada,
    dist_compra_contra,
    dist_venda_contra,
    dist_favor_compra,
    dist_favor_venda,
    referencia,
    horarios_selecionados,
    data_inicio,
    data_fim,
    modo_estrategia,
    usar_filtro_liquidez,
    limite_liquidez
):
    todas_operacoes = []
    dias_com_entrada = set()
    dias_ignorados = []
    todos_dias_com_dados = set()
    arquivos_ignorados = []
    mensagens_liquidez = []

    # ========================
    # OTIMIZAÇÃO: ler cada arquivo APENAS UMA VEZ
    # ========================
    arquivos_processados = {}

    def carregar_arquivo(file):
        try:
            # ✅ Se for FakeFile (vindo do Yahoo Finance)
            if hasattr(file, "df"):
                df = file.df.copy()
            # ✅ Se for arquivo real (upload Excel)
            else:
                df = pd.read_excel(file)

            # Normalizar nomes das colunas
            df.columns = [str(col).strip().capitalize() for col in df.columns]
            df.rename(columns={
                'Data': 'data',
                'Abertura': 'open',
                'Máxima': 'high',
                'Mínima': 'low',
                'Fechamento': 'close',
                'Volume': 'volume'
            }, inplace=True)

            # Converter coluna de data
            df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['data'])
            df['data_limpa'] = df['data'].dt.floor('min')
            df = df.set_index('data_limpa').sort_index()
            df = df[~df.index.duplicated(keep='first')]
            if df.index.tz:
                df = df.tz_localize(None)
            df['data_sozinha'] = df.index.date
            df = df[(df['data_sozinha'] >= data_inicio) & (df['data_sozinha'] <= data_fim)]
            return df
        except Exception as e:
            st.error(f"❌ Erro ao processar {getattr(file, 'name', 'arquivo desconhecido')}: {e}")
            return None

    with ThreadPoolExecutor() as executor:
        future_to_file = {executor.submit(carregar_arquivo, file): file for file in uploaded_files}
        for future in as_completed(future_to_file):
            file = future_to_file[future]
            df = future.result()
            if df is not None:
                arquivos_processados[file] = df

    def calcular_max_drawdown(df, idx_entrada, idx_saida, direcao):
        try:
            periodo = df.loc[idx_entrada:idx_saida]
            if periodo.empty or len(periodo) < 2:
                return 0.0
            preco_entrada = periodo.iloc[0]["open"]
            if direcao == "Compra":
                min_preco = periodo["low"].min()
                drawdown = ((min_preco - preco_entrada) / preco_entrada) * 100
            else:
                max_preco = periodo["high"].max()
                drawdown = ((max_preco - preco_entrada) / preco_entrada) * 100
            return round(drawdown, 2)
        except:
            return 0.0

    for horario_str in horarios_selecionados:
        hora, minuto = map(int, horario_str.split(":"))
        hora_inicio = time_obj(hora, minuto)
        for file, df in arquivos_processados.items():
            try:
                ticker_nome = extrair_nome_completo(file.name)
                tipo_arquivo = identificar_tipo(ticker_nome)
                if tipo_ativo != "todos" and tipo_arquivo != tipo_ativo:
                    if file.name not in arquivos_ignorados:
                        arquivos_ignorados.append(file.name)
                    continue
                if df.empty:
                    continue

                if usar_filtro_liquidez:
                    col_volume_acoes = None
                    col_volume_financeiro = None
                    for col in df.columns:
                        col_lower = col.lower().strip()
                        if col_lower in ['volume', 'vol', 'quantidade', 'negocios', 'negócios']:
                            col_volume_acoes = col
                        elif col_lower in ['volume financeiro', 'vol financeiro', 'valor negociado', 'valor', 'vlr negociado', 'volume_r$', 'volume_financ', 'volume financeiro (r$)']:
                            col_volume_financeiro = col

                    if col_volume_financeiro is not None:
                        df['Volume_Financeiro'] = pd.to_numeric(df[col_volume_financeiro], errors='coerce')
                        volume_clean = df['Volume_Financeiro'].dropna()
                        if volume_clean.empty:
                            mensagens_liquidez.append(f"ℹ️ {ticker_nome}: dados de 'Volume Financeiro' estão vazios")
                        else:
                            df['data_sozinha'] = df.index.date
                            volume_diario = df.groupby('data_sozinha')['Volume_Financeiro'].sum()
                            valor_medio_diario = volume_diario.mean()
                            if valor_medio_diario < limite_liquidez:
                                mensagens_liquidez.append(f"⚠️ {ticker_nome}: baixa liquidez (R$ {valor_medio_diario:,.0f}/dia) → ignorado")
                                continue
                            else:
                                mensagens_liquidez.append(f"✅ {ticker_nome}: liquidez OK (R$ {valor_medio_diario:,.0f}/dia)")
                    elif col_volume_acoes is not None:
                        df['Volume_Acoes'] = pd.to_numeric(df[col_volume_acoes], errors='coerce')
                        volume_clean = df['Volume_Acoes'].dropna()
                        if volume_clean.empty:
                            mensagens_liquidez.append(f"ℹ️ {ticker_nome}: dados de volume estão vazios")
                        else:
                            df['data_sozinha'] = df.index.date
                            volume_diario = df.groupby('data_sozinha')['Volume_Acoes'].sum()
                            volume_medio = volume_diario.mean()
                            preco_medio = df['close'].mean()
                            valor_medio_diario = volume_medio * preco_medio
                            if valor_medio_diario < limite_liquidez:
                                mensagens_liquidez.append(f"⚠️ {ticker_nome}: baixa liquidez (R$ {valor_medio_diario:,.0f}/dia) → ignorado")
                                continue
                            else:
                                mensagens_liquidez.append(f"✅ {ticker_nome}: liquidez OK (R$ {valor_medio_diario:,.0f}/dia)")
                    else:
                        mensagens_liquidez.append(f"ℹ️ {ticker_nome}: coluna de volume não encontrada")

                dias_no_arquivo = df['data_sozinha'].unique()
                todos_dias_com_dados.update(dias_no_arquivo)
                dias_unicos = pd.unique(df['data_sozinha'])
                for i in range(1, len(dias_unicos)):
                    dia_atual = dias_unicos[i]
                    dia_anterior = dias_unicos[i - 1]
                    df_dia_atual = df[df['data_sozinha'] == dia_atual].copy()

                    if tipo_ativo in ['mini_indice', 'mini_dolar']:
                        mascara_pregao = (df_dia_atual.index.time >= time_obj(9, 0)) & (df_dia_atual.index.time <= time_obj(18, 20))
                    else:
                        mascara_pregao = (df_dia_atual.index.time >= time_obj(10, 0)) & (df_dia_atual.index.time <= time_obj(17, 0))

                    df_pregao = df_dia_atual[mascara_pregao]
                    if df_pregao.empty:
                        dias_ignorados.append((dia_atual, "Sem pregão válido"))
                        continue

                    def time_to_minutes(t):
                        return t.hour * 60 + t.minute

                    minutos_desejado = time_to_minutes(hora_inicio)
                    minutos_candles = [time_to_minutes(t) for t in df_pregao.index.time]
                    diferencas = [abs(m - minutos_desejado) for m in minutos_candles]
                    melhor_idx = np.argmin(diferencas)
                    idx_entrada = df_pregao.index[melhor_idx]
                    preco_entrada = df_pregao.loc[idx_entrada]["open"]
                    idx_saida = idx_entrada + pd.Timedelta(minutes=5 * int(candles_pos_entrada))

                    if idx_saida not in df.index or idx_saida.date() != idx_entrada.date():
                        dias_ignorados.append((dia_atual, "Sem candle de saída"))
                        continue

                    if tipo_ativo in ['mini_indice', 'mini_dolar'] and idx_saida.time() > time_obj(18, 20):
                        dias_ignorados.append((dia_atual, "Candle de saída após 18:20"))
                        continue
                    elif tipo_ativo == 'acoes' and idx_saida.time() > time_obj(17, 0):
                        dias_ignorados.append((dia_atual, "Candle de saída após 17:00"))
                        continue

                    preco_saida = df.loc[idx_saida]["open"]
                    referencia_valor = None
                    referencia_label = ""
                    if referencia == "Fechamento do dia anterior":
                        ref_series = df[df.index.date == dia_anterior]["close"]
                        if not ref_series.empty:
                            referencia_valor = ref_series.iloc[-1]
                            referencia_label = f"Fechamento {dia_anterior.strftime('%d/%m')}: {referencia_valor:.2f}"
                        else:
                            dias_ignorados.append((dia_atual, "Sem fechamento do dia anterior"))
                            continue
                    elif referencia == "Mínima do dia anterior":
                        ref_series = df[df.index.date == dia_anterior]["low"]
                        if not ref_series.empty:
                            referencia_valor = ref_series.min()
                            referencia_label = f"Mínima {dia_anterior.strftime('%d/%m')}: {referencia_valor:.2f}"
                        else:
                            dias_ignorados.append((dia_atual, "Sem mínima do dia anterior"))
                            continue
                    elif referencia == "Abertura do dia atual":
                        if not df_dia_atual["open"].empty:
                            referencia_valor = df_dia_atual["open"].iloc[0]
                            referencia_label = f"Abertura {dia_atual.strftime('%d/%m')}: {referencia_valor:.2f}"
                        else:
                            dias_ignorados.append((dia_atual, "Sem abertura do dia atual"))
                            continue

                    if referencia_valor is None or referencia_valor <= 0:
                        dias_ignorados.append((dia_atual, "Referência inválida"))
                        continue

                    distorcao_percentual = ((preco_entrada - referencia_valor) / referencia_valor) * 100
                    horario_entrada_str = idx_entrada.strftime("%H:%M")

                    if horario_entrada_str not in horarios_selecionados:
                        continue

                    if tipo_ativo == "acoes":
                        valor_ponto = 1.0
                    else:
                        valor_ponto = 0.20 if tipo_ativo == "mini_indice" else 10.00

                    if modo_estrategia in ["A Favor da Tendência", "Ambos"]:
                        if distorcao_percentual > dist_favor_compra:
                            lucro_reais = (preco_saida - preco_entrada) * valor_ponto * qtd
                            max_dd = calcular_max_drawdown(df, idx_entrada, idx_saida, "Compra")
                            todas_operacoes.append({
                                "Ação": ticker_nome,
                                "Direção": "Compra (Favor)",
                                "Horário": horario_entrada_str,
                                "Data Entrada": idx_entrada.strftime("%d/%m/%Y %H:%M"),
                                "Data Saída": idx_saida.strftime("%d/%m/%Y %H:%M"),
                                "Preço Entrada": round(preco_entrada, 2),
                                "Preço Saída": round(preco_saida, 2),
                                "Lucro (R$)": round(lucro_reais, 2),
                                "Distorção (%)": f"{distorcao_percentual:.2f}%",
                                "Quantidade": qtd,
                                "Referência": referencia_label,
                                "Max Drawdown %": max_dd
                            })
                            dias_com_entrada.add(dia_atual)
                        elif distorcao_percentual < -dist_favor_venda:
                            lucro_reais = (preco_entrada - preco_saida) * valor_ponto * qtd
                            max_dd = calcular_max_drawdown(df, idx_entrada, idx_saida, "Venda")
                            todas_operacoes.append({
                                "Ação": ticker_nome,
                                "Direção": "Venda (Favor)",
                                "Horário": horario_entrada_str,
                                "Data Entrada": idx_entrada.strftime("%d/%m/%Y %H:%M"),
                                "Data Saída": idx_saida.strftime("%d/%m/%Y %H:%M"),
                                "Preço Entrada": round(preco_entrada, 2),
                                "Preço Saída": round(preco_saida, 2),
                                "Lucro (R$)": round(lucro_reais, 2),
                                "Distorção (%)": f"{distorcao_percentual:.2f}%",
                                "Quantidade": qtd,
                                "Referência": referencia_label,
                                "Max Drawdown %": max_dd
                            })
                            dias_com_entrada.add(dia_atual)

                    if modo_estrategia in ["Contra Tendência", "Ambos"]:
                        if distorcao_percentual < -dist_compra_contra:
                            lucro_reais = (preco_saida - preco_entrada) * valor_ponto * qtd
                            max_dd = calcular_max_drawdown(df, idx_entrada, idx_saida, "Compra")
                            todas_operacoes.append({
                                "Ação": ticker_nome,
                                "Direção": "Compra (Contra)",
                                "Horário": horario_entrada_str,
                                "Data Entrada": idx_entrada.strftime("%d/%m/%Y %H:%M"),
                                "Data Saída": idx_saida.strftime("%d/%m/%Y %H:%M"),
                                "Preço Entrada": round(preco_entrada, 2),
                                "Preço Saída": round(preco_saida, 2),
                                "Lucro (R$)": round(lucro_reais, 2),
                                "Distorção (%)": f"{distorcao_percentual:.2f}%",
                                "Quantidade": qtd,
                                "Referência": referencia_label,
                                "Max Drawdown %": max_dd
                            })
                            dias_com_entrada.add(dia_atual)
                        elif distorcao_percentual > dist_venda_contra:
                            lucro_reais = (preco_entrada - preco_saida) * valor_ponto * qtd
                            max_dd = calcular_max_drawdown(df, idx_entrada, idx_saida, "Venda")
                            todas_operacoes.append({
                                "Ação": ticker_nome,
                                "Direção": "Venda (Contra)",
                                "Horário": horario_entrada_str,
                                "Data Entrada": idx_entrada.strftime("%d/%m/%Y %H:%M"),
                                "Data Saída": idx_saida.strftime("%d/%m/%Y %H:%M"),
                                "Preço Entrada": round(preco_entrada, 2),
                                "Preço Saída": round(preco_saida, 2),
                                "Lucro (R$)": round(lucro_reais, 2),
                                "Distorção (%)": f"{distorcao_percentual:.2f}%",
                                "Quantidade": qtd,
                                "Referência": referencia_label,
                                "Max Drawdown %": max_dd
                            })
                            dias_com_entrada.add(dia_atual)
            except Exception as e:
                st.write(f"❌ Erro ao processar {file.name}: {e}")
                continue

    if usar_filtro_liquidez and mensagens_liquidez:
        with st.expander("📊 Detalhes do Filtro de Liquidez", expanded=False):
            for msg in mensagens_liquidez:
                if "✅" in msg:
                    st.markdown(f"<span style='color: green;'>{msg}</span>", unsafe_allow_html=True)
                elif "⚠️" in msg:
                    st.markdown(f"<span style='color: orange;'>{msg}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color: gray;'>{msg}</span>", unsafe_allow_html=True)

    for file_name in arquivos_ignorados:
        ticker_nome = extrair_nome_completo(file_name)
        tipo_arquivo = identificar_tipo(ticker_nome)
        st.warning(f"⚠️ Arquivo ignorado ({file_name}): é um **{tipo_arquivo.replace('_', ' ').title()}**, mas você selecionou **{tipo_ativo.replace('_', ' ').title()}**.")

    df_ops = pd.DataFrame(todas_operacoes)
    return df_ops, list(dias_com_entrada), dias_ignorados, sorted(todos_dias_com_dados)

# ========================
# SISTEMA PRINCIPAL
# ========================
def sistema_principal():
    if 'intraday_executado' not in st.session_state:
        st.session_state.intraday_executado = True

    st.success("✅ Acesso liberado")
    st.write(f"📆 Expira em: **{st.session_state.expira.strftime('%d/%m/%Y')}**")
    st.markdown(f"Olá, **{st.session_state.email}**! Bem-vindo ao Radar B3.")

    plano = st.session_state.plano
    if plano == "Diamante":
        modo_sistema = st.selectbox(
            "Modo de Operação",
            ["Diamante - Diário", "Diamante - Intraday"],
            key="modo_sistema_intraday_teste_unico"
        )
    else:
        modo_sistema = "Plano Bronze"

    if modo_sistema in ["Plano Bronze", "Plano Prata", "Plano Ouro", "Diamante - Diário"]:
        st.info("Este é um teste do Intraday. O Diário está oculto.")
    elif modo_sistema == "Diamante - Intraday":
        if plano != "Diamante":
            st.error("❌ Acesso ao modo Intraday é exclusivo para o Plano Diamante.")
            st.stop()

        # === DADOS DO YAHOO FINANCE (sem upload) ===
        st.info("📡 Dados carregados automaticamente do Yahoo Finance (candles de 5min - últimos 60 dias)")

        ticker_input = st.text_input("Digite o ativo (ex: PETR4, WINM24, WDOF24):", value="PETR4").strip()
        if not ticker_input:
            st.info("Por favor, digite um ativo para continuar.")
            st.stop()

        # Ajusta o ticker: PETR4 → PETR4.SA | WINM24 → WINM24
        ticker = ajustar_ticker(ticker_input)
        nome_exibicao = ticker_input.upper()

        with st.spinner(f"Baixando dados de `{ticker}`..."):
            try:
                data = yf.download(ticker, period="60d", interval="5m", auto_adjust=True, progress=False)
                if data.empty:
                    st.error(f"⚠️ Nenhum dado encontrado para `{ticker}`. Verifique o nome do ativo.")
                    st.stop()

                data_reset = data.reset_index()

                # Detectar coluna de data automaticamente
                datetime_col = None
                for col in data_reset.columns:
                    if pd.api.types.is_datetime64_any_dtype(data_reset[col]):
                        datetime_col = col
                        break
                if datetime_col is None:
                    for col in data_reset.columns:
                        coerced = pd.to_datetime(data_reset[col], errors='coerce', dayfirst=True)
                        if coerced.notna().sum() > 0:
                            data_reset[col] = coerced
                            datetime_col = col
                            break
                if datetime_col is None and isinstance(data.index, pd.DatetimeIndex):
                    data_reset.insert(0, 'Data', data.index)
                    datetime_col = 'Data'
                if datetime_col is None:
                    st.error("❌ Erro: coluna de data não encontrada nos dados do Yahoo.")
                    st.stop()
                if datetime_col != 'Data':
                    data_reset.rename(columns={datetime_col: 'Data'}, inplace=True)

                # Renomear colunas com mapeamento flexível
                rename_map = {}
                for c in data_reset.columns:
                    lc = str(c).lower()
                    if 'open' in lc or 'abert' in lc: rename_map[c] = 'Abertura'
                    if 'high' in lc or 'max' in lc: rename_map[c] = 'Máxima'
                    if 'low' in lc or 'min' in lc: rename_map[c] = 'Mínima'
                    if 'close' in lc or 'fech' in lc: rename_map[c] = 'Fechamento'
                    if 'volume' in lc or lc == 'vol': rename_map[c] = 'Volume'
                data_reset.rename(columns=rename_map, inplace=True)

                # Converter e limpar
                data_reset['Data'] = pd.to_datetime(data_reset['Data'], errors='coerce', dayfirst=True)
                data_reset = data_reset.dropna(subset=['Data']).copy()
                if data_reset.empty:
                    st.error("⚠️ Nenhum dado válido após conversão da data.")
                    st.stop()

                # Simular "arquivo" para compatibilidade
                class FakeFile:
                    def __init__(self, name, df):
                        self.name = name
                        self.df = df

                fake_file = FakeFile(f"{nome_exibicao}.xlsx", data_reset)
                uploaded_files = [fake_file]

                st.success(f"✅ Dados de `{nome_exibicao}` carregados com sucesso! 📊 Total: {len(data_reset)} candles de 5min")

            except Exception as e:
                st.error(f"❌ Erro ao baixar ou processar dados: {e}")
                st.stop()

        # Lê o período real dos dados baixados
        data_min_global = None
        data_max_global = None
        for file in uploaded_files:
            try:
                df_temp = file.df.copy()
                df_temp['data'] = pd.to_datetime(df_temp['Data'], dayfirst=True, errors='coerce')
                df_temp = df_temp.dropna(subset=['data'])
                df_temp['data_sozinha'] = df_temp['data'].dt.date
                min_data = df_temp['data_sozinha'].min()
                max_data = df_temp['data_sozinha'].max()
                if data_min_global is None or min_data < data_min_global:
                    data_min_global = min_data
                if data_max_global is None or max_data > data_max_global:
                    data_max_global = max_data
            except Exception as e:
                st.warning(f"⚠️ Erro ao processar {file.name}: {e}")

        if data_min_global and data_max_global:
            st.subheader("📅 Período disponível")
            st.write(f"**Início:** {data_min_global.strftime('%d/%m/%Y')}")
            st.write(f"**Fim:** {data_max_global.strftime('%d/%m/%Y')}")
            st.subheader("🔍 Filtro de período")
            data_inicio = st.date_input("Data inicial", value=data_min_global, min_value=data_min_global, max_value=data_max_global)
            data_fim = st.date_input("Data final", value=data_max_global, min_value=data_min_global, max_value=data_max_global)

            if isinstance(data_inicio, datetime):
                data_inicio = data_inicio.date()
            if isinstance(data_fim, datetime):
                data_fim = data_fim.date()

            if data_inicio > data_fim:
                st.error("❌ A data inicial não pode ser maior que a final.")
                st.stop()

            st.header("⚙️ Configure o Rastreamento")

            # Calcular horários válidos
            fim_pregao = {
                'acoes': time_obj(17, 0),
                'mini_indice': time_obj(18, 20),
                'mini_dolar': time_obj(18, 20)
            }
            horarios_validos = [f"{h:02d}:{m:02d}" for h in range(9, 19) for m in range(0, 60, 5)]

            with st.form("configuracoes"):
                tipo_ativo = st.selectbox("Tipo de ativo", ["acoes", "mini_indice", "mini_dolar"])
                qtd = st.number_input("Quantidade", min_value=1, value=1)
                candles_pos_entrada = st.number_input("Candles após entrada", min_value=1, value=3)

                # Atualizar último horário com base no tipo
                ultimo_horario_entrada = (datetime.combine(datetime.today(), fim_pregao[tipo_ativo]) - pd.Timedelta(minutes=5 * int(candles_pos_entrada))).time()
                horarios_filtrados = [h for h in horarios_validos if datetime.strptime(h, '%H:%M').time() <= ultimo_horario_entrada]

                if len(horarios_filtrados) == 0:
                    st.warning("⚠️ Nenhum horário válido disponível com esse número de candles.")
                    st.stop()

                st.info(f"✅ Horários válidos até **{ultimo_horario_entrada.strftime('%H:%M')}** para saída dentro do pregão.")

                horarios_selecionados = st.multiselect(
                    "Horários de análise",
                    options=horarios_filtrados,
                    default=[h for h in ["09:00", "09:05", "10:55", "11:00", "11:05"] if h in horarios_filtrados]
                )
                modo_estrategia = st.selectbox(
                    "Modo da Estratégia",
                    ["Contra Tendência", "A Favor da Tendência", "Ambos"]
                )
                if modo_estrategia in ["A Favor da Tendência", "Ambos"]:
                    dist_favor_compra = st.number_input("Distorção mínima COMPRA (%) - A Favor", value=0.5)
                    dist_favor_venda = st.number_input("Distorção mínima VENDA (%) - A Favor", value=0.5)
                else:
                    dist_favor_compra = dist_favor_venda = 0.0
                if modo_estrategia in ["Contra Tendência", "Ambos"]:
                    dist_compra_contra = st.number_input("Distorção mínima COMPRA (%) - Contra", value=0.3)
                    dist_venda_contra = st.number_input("Distorção mínima VENDA (%) - Contra", value=0.3)
                else:
                    dist_compra_contra = dist_venda_contra = 0.0
                referencia = st.selectbox(
                    "Referência da distorção",
                    ["Fechamento do dia anterior", "Mínima do dia anterior", "Abertura do dia atual"]
                )
                usar_filtro_liquidez = st.checkbox("Filtrar por liquidez mínima?", value=False)
                limite_liquidez = st.number_input(
                    "Liquidez mínima diária (R$)",
                    min_value=0,
                    value=50000,
                    help="Ignora ativos com volume diário médio inferior a este valor.",
                    disabled=not usar_filtro_liquidez
                )
                submitted = st.form_submit_button("✅ Aplicar Configurações")

            if submitted:
                if not horarios_selecionados:
                    st.warning("⚠️ Selecione pelo menos um horário.")
                else:
                    st.session_state.configuracoes_salvas = {
                        "tipo_ativo": tipo_ativo,
                        "qtd": qtd,
                        "candles_pos_entrada": candles_pos_entrada,
                        "dist_compra_contra": dist_compra_contra,
                        "dist_venda_contra": dist_venda_contra,
                        "dist_favor_compra": dist_favor_compra,
                        "dist_favor_venda": dist_favor_venda,
                        "referencia": referencia,
                        "horarios_selecionados": horarios_selecionados,
                        "modo_estrategia": modo_estrategia,
                        "usar_filtro_liquidez": usar_filtro_liquidez,
                        "limite_liquidez": limite_liquidez
                    }
                    st.success("✅ Configurações aplicadas!")

            if "configuracoes_salvas" in st.session_state:
                if st.button("🔍 Iniciar Rastreamento"):
                    cfg = st.session_state.configuracoes_salvas
                    with st.spinner("📡 Rastreando padrões de mercado..."):
                        df_ops, dias_com_entrada, dias_ignorados, todos_dias_com_dados = processar_rastreamento_intraday(
                            uploaded_files=uploaded_files,
                            tipo_ativo=cfg["tipo_ativo"],
                            qtd=cfg["qtd"],
                            candles_pos_entrada=cfg["candles_pos_entrada"],
                            dist_compra_contra=cfg["dist_compra_contra"],
                            dist_venda_contra=cfg["dist_venda_contra"],
                            dist_favor_compra=cfg["dist_favor_compra"],
                            dist_favor_venda=cfg["dist_favor_venda"],
                            referencia=cfg["referencia"],
                            horarios_selecionados=cfg["horarios_selecionados"],
                            data_inicio=data_inicio,
                            data_fim=data_fim,
                            modo_estrategia=cfg["modo_estrategia"],
                            usar_filtro_liquidez=cfg["usar_filtro_liquidez"],
                            limite_liquidez=cfg["limite_liquidez"]
                        )
                    if not df_ops.empty:
                        df_ops = df_ops[df_ops['Horário'].isin(cfg["horarios_selecionados"])].copy()
                        st.session_state.todas_operacoes = df_ops
                        st.success(f"✅ Rastreamento concluído: {len(df_ops)} oportunidades detectadas.")
                        for col in ['Preço Entrada', 'Preço Saída', 'Lucro (R$)', 'Max Drawdown %']:
                            if col in df_ops.columns and df_ops[col].dtype == 'object':
                                df_ops[col] = pd.to_numeric(df_ops[col].astype(str).str.replace(',', '.'), errors='coerce')
                        st.markdown("### 📊 Resumo Consolidado por Horário de Entrada")
                        resumo = df_ops.groupby(['Horário', 'Ação', 'Direção'], as_index=False).agg(
                            Total_Eventos=('Lucro (R$)', 'count'),
                            Acertos=('Lucro (R$)', lambda x: (x > 0).sum()),
                            Lucro_Total=('Lucro (R$)', 'sum'),
                            Max_DD_Medio=('Max Drawdown %', 'mean')
                        )
                        def icone_resumo(row):
                            if 'Contra' in row['Direção']:
                                return '🔽🟢' if 'Compra' in row['Direção'] else '🔼🔴'
                            elif 'Favor' in row['Direção']:
                                return '🔼🟢' if 'Compra' in row['Direção'] else '🔽🔴'
                            return '⚪'
                        resumo[' '] = resumo.apply(icone_resumo, axis=1)
                        resumo['Taxa de Acerto'] = (resumo['Acertos'] / resumo['Total_Eventos']).map('{:.2%}'.format)
                        resumo['Lucro Total (R$)'] = resumo['Lucro_Total'].map(lambda x: f"R$ {x:.2f}")
                        resumo['Ganho Médio por Trade (R$)'] = (resumo['Lucro_Total'] / resumo['Total_Eventos']).map(lambda x: f"R$ {x:+.2f}")
                        resumo['Máx. Drawdown Médio (%)'] = resumo['Max_DD_Medio'].map(lambda x: f"{x:+.2f}%")
                        resumo = resumo[[
                            ' ', 'Horário', 'Ação', 'Direção', 'Total_Eventos', 'Acertos', 'Taxa de Acerto',
                            'Lucro Total (R$)', 'Ganho Médio por Trade (R$)', 'Máx. Drawdown Médio (%)'
                        ]]
                        def cor_resumo(row):
                            try:
                                valor = float(row['Lucro Total (R$)'].replace('R$', '').strip())
                            except:
                                valor = 0.0
                            cor = '#d4edda' if valor > 0 else '#f8d7da' if valor < 0 else '#fff3cd'
                            return [f'background-color: {cor}'] * len(row)
                        st.dataframe(
                            resumo.style.apply(cor_resumo, axis=1),
                            use_container_width=True,
                            hide_index=True
                        )
                        with st.expander("ℹ️ O que significam os ícones?"):
                            st.markdown("""
                            - **🔽🟢** = Compra (Contra) → Reversão (espera recuperação)  
                            - **🔼🔴** = Venda (Contra) → Reversão (espera correção)  
                            - **🔼🟢** = Compra (Favor) → A Favor da Tendência (acompanha alta)  
                            - **🔽🔴** = Venda (Favor) → A Favor da Tendência (acompanha queda)  
                            """)
                        csv_data = df_ops.to_csv(index=False, sep=";", decimal=",", encoding='utf-8-sig')
                        st.download_button(
                            label="📥 Exportar Resultados para CSV",
                            data=csv_data,
                            file_name="resultados_intraday.csv",
                            mime="text/csv"
                        )
                        with st.expander("📊 Análise de Dias"):
                            st.write("Dias com entrada e saída válida:", len(dias_com_entrada))
                            if dias_ignorados:
                                st.write("Dias ignorados:")
                                for dia, motivo in dias_ignorados[:10]:
                                    st.write(f"- {dia.strftime('%d/%m')} → {motivo}")
                        if not df_ops.empty:
                            with st.expander("🔍 Ver oportunidades detalhadas (Intraday)"):
                                df_detalhe = df_ops.copy()
                                df_detalhe['Lucro (R$)'] = pd.to_numeric(df_detalhe['Lucro (R$)'], errors='coerce')
                                df_detalhe['Acerto?'] = df_detalhe['Lucro (R$)'].apply(
                                    lambda x: '✅ Sim' if x > 0 else '❌ Não' if x < 0 else '➖ Neutro'
                                )
                                cols = list(df_detalhe.columns)
                                lucro_idx = cols.index('Lucro (R$)')
                                cols.insert(lucro_idx + 1, cols.pop(cols.index('Acerto?')))
                                df_detalhe = df_detalhe[cols]
                                def icone_detalhe(row):
                                    if 'Contra' in row['Direção']:
                                        return '🔽🟢' if 'Compra' in row['Direção'] else '🔼🔴'
                                    elif 'Favor' in row['Direção']:
                                        return '🔼🟢' if 'Compra' in row['Direção'] else '🔽🔴'
                                    return '⚪'
                                df_detalhe[' '] = df_detalhe.apply(icone_detalhe, axis=1)
                                cols = [' '] + [col for col in df_detalhe.columns if col != ' ']
                                df_exibir = df_detalhe[cols]
                                def cor_linha(row):
                                    valor = row['Lucro (R$)']
                                    if valor > 0:
                                        return ['background-color: #d4edda'] * len(row)
                                    elif valor < 0:
                                        return ['background-color: #f8d7da'] * len(row)
                                    else:
                                        return ['background-color: #fff3cd'] * len(row)
                                st.dataframe(
                                    df_exibir.style.apply(cor_linha, axis=1),
                                    use_container_width=True,
                                    hide_index=True
                                )

# ========================
# EXECUÇÃO
# ========================
if __name__ == "__main__":
    sistema_principal()
