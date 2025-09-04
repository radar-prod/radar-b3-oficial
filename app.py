# ========================
# TESTE SOMENTE INTRADAY
# ========================
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, time as time_obj, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========================
# SIMULAÇÃO DE LOGIN (com expiração em 2099)
# ========================
if "email" not in st.session_state:
    st.session_state.email = "teste@gmail.com"
    st.session_state.plano = "Diamante"
    st.session_state.expira = datetime(2099, 12, 31).date()  # ✅ Expira em 31/12/2099
    st.rerun()

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
# FUNÇÃO: Verificar lacunas
# ========================
def verificar_lacunas(uploaded_files, abertura_acoes, fechamento_acoes, abertura_mini, fechamento_mini):
    with st.expander("🔍 Validação de Dados: Status por Arquivo"):
        st.markdown("### 📂 Resumo de Integridade dos Arquivos")
        total_analisados = 0
        total_com_lacuna = 0
        total_erro = 0
        for file in uploaded_files:
            try:
                excel = pd.ExcelFile(file)
                df = None
                for sheet in excel.sheet_names:
                    try:
                        temp_df = pd.read_excel(excel, sheet_name=sheet)
                        if not temp_df.empty and 'Data' in temp_df.columns:
                            df = temp_df
                            break
                    except:
                        continue
                if df is None:
                    st.markdown(f"❌ **{file.name}** → ❌ Nenhuma aba com coluna 'Data' encontrada")
                    total_erro += 1
                    continue
                if 'Data' not in df.columns:
                    st.markdown(f"❌ **{file.name}** → ❌ Coluna 'Data' não encontrada")
                    total_erro += 1
                    continue
                df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
                if df['Data'].isna().all():
                    st.markdown(f"❌ **{file.name}** → ⚠️ Coluna 'Data' não pôde ser convertida")
                    total_erro += 1
                    continue
                df = df.dropna(subset=['Data'])
                if df.empty:
                    st.markdown(f"❌ **{file.name}** → ⚠️ Dados vazios após limpeza")
                    total_erro += 1
                    continue
                df['datetime'] = df['Data'].dt.floor('min')
                df = df.drop_duplicates(subset=['datetime'])
                df = df.set_index('datetime').sort_index()
                ticker_detectado = identificar_tipo(file.name)
                if ticker_detectado == 'acoes':
                    inicio_pregao = abertura_acoes
                    fim_pregao = fechamento_acoes
                elif ticker_detectado in ['mini_indice', 'mini_dolar']:
                    inicio_pregao = abertura_mini
                    fim_pregao = fechamento_mini
                else:
                    inicio_pregao = abertura_acoes
                    fim_pregao = fechamento_acoes
                mascara_pregao = ((df.index.time >= inicio_pregao) & (df.index.time <= fim_pregao))
                df_filtrado = df[mascara_pregao]
                if df_filtrado.empty:
                    st.markdown(f"🟡 **{file.name}** → ⚠️ Nenhum dado dentro do horário de pregão ({inicio_pregao.strftime('%H:%M')} - {fim_pregao.strftime('%H:%M')})")
                    total_com_lacuna += 1
                    total_analisados += 1
                    continue
                df_filtrado['data_sozinha'] = df_filtrado.index.date
                datas = df_filtrado['data_sozinha'].unique()
                total_dias = len(datas)
                dias_com_lacuna = 0
                detalhes_lacunas = []
                for dia in datas:
                    df_dia = df_filtrado[df_filtrado['data_sozinha'] == dia].copy()
                    if df_dia.empty:
                        continue
                    horarios_reais = set(df_dia.index.time)
                    inicio = datetime.combine(dia, inicio_pregao)
                    fim = datetime.combine(dia, fim_pregao)
                    horarios_esperados = []
                    atual = inicio
                    while atual <= fim:
                        horarios_esperados.append(atual.time())
                        atual += timedelta(minutes=5)
                    faltando = [h for h in horarios_esperados if h not in horarios_reais]
                    if faltando:
                        dias_com_lacuna += 1
                        horarios_faltando_str = ", ".join([h.strftime('%H:%M') for h in faltando[:5]])
                        if len(faltando) > 5:
                            horarios_faltando_str += f" +{len(faltando)-5}"
                        detalhes_lacunas.append(f"  → {dia.strftime('%d/%m/%Y')} → {horarios_faltando_str}")
                if dias_com_lacuna == 0:
                    st.markdown(f"✅ **{file.name}** → **{total_dias} dia(s)** → Todos os candles no pregão estão completos")
                else:
                    st.markdown(f"🟡 **{file.name}** → **{total_dias} dia(s)** → **{dias_com_lacuna} com lacunas** ⚠️")
                    with st.expander(f"Detalhes: clique para ver onde faltam candles"):
                        for linha in detalhes_lacunas:
                            st.markdown(f"<small>{linha}</small>", unsafe_allow_html=True)
                    total_com_lacuna += 1
                total_analisados += 1
            except Exception as e:
                st.markdown(f"❌ **{file.name}** → ❓ Erro: {type(e).__name__}: {str(e)}")
                total_erro += 1
        st.divider()
        st.markdown("### 📊 **Resumo Geral**")
        st.markdown(f"- ✅ **{total_analisados} arquivos analisados**")
        st.markdown(f"- ⚠️ Arquivos com lacunas: **{total_com_lacuna}**")
        st.markdown(f"- ❌ Arquivos com erro: **{total_erro}**")

# ========================
# FUNÇÃO DE RASTREAMENTO INTRADAY
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
    # (mantido para integração futura)
    pass

# ========================
# SISTEMA PRINCIPAL
# ========================
def sistema_principal():
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

    # ============ MODO DIÁRIO ============
    if modo_sistema in ["Plano Bronze", "Plano Prata", "Plano Ouro", "Diamante - Diário"]:
        st.info("Este é um teste do Intraday. O Diário está oculto.")

    # ============ MODO INTRADAY ============
    elif modo_sistema == "Diamante - Intraday":
        if plano != "Diamante":
            st.error("❌ Acesso ao modo Intraday é exclusivo para o Plano Diamante.")
            st.stop()

        st.header("📤 Carregue seus Dados (Excel 5min)")
        uploaded_files = st.file_uploader("Escolha um ou mais arquivos .xlsx", type=["xlsx"], accept_multiple_files=True)

        if uploaded_files:
            st.info(f"✅ {len(uploaded_files)} arquivo(s) carregado(s).")

            # ✅ Garantir que os horários estão no session_state
            if 'abertura_acoes' not in st.session_state:
                st.session_state.abertura_acoes = time_obj(10, 0)
            if 'fechamento_acoes' not in st.session_state:
                st.session_state.fechamento_acoes = time_obj(17, 0)
            if 'abertura_mini' not in st.session_state:
                st.session_state.abertura_mini = time_obj(9, 0)
            if 'fechamento_mini' not in st.session_state:
                st.session_state.fechamento_mini = time_obj(18, 20)

            # ✅ Configurar horários
            st.subheader("⏰ Configurar Horários de Pregão")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Ações**")
                st.time_input("Abertura", value=st.session_state.abertura_acoes, key="abertura_acoes")
                st.time_input("Fechamento", value=st.session_state.fechamento_acoes, key="fechamento_acoes")

            with col2:
                st.markdown("**Mini Índice / Mini Dólar**")
                st.time_input("Abertura", value=st.session_state.abertura_mini, key="abertura_mini")
                st.time_input("Fechamento", value=st.session_state.fechamento_mini, key="fechamento_mini")

            # ✅ BOTÃO DE VALIDAÇÃO
            if st.button("🔍 Validar Arquivos (Verificar Lacunas)"):
                with st.spinner("Verificando integridade dos dados..."):
                    verificar_lacunas(
                        uploaded_files,
                        st.session_state.abertura_acoes,
                        st.session_state.fechamento_acoes,
                        st.session_state.abertura_mini,
                        st.session_state.fechamento_mini
                    )

            # Lê o período real dos arquivos
            data_min_global = None
            data_max_global = None
            for file in uploaded_files:
                try:
                    df_temp = pd.read_excel(file)
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
                    st.warning(f"⚠️ Erro ao ler {file.name}: {e}")

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

                with st.form("configuracoes"):
                    tipo_ativo = st.selectbox("Tipo de ativo", ["acoes", "mini_indice", "mini_dolar"])
                    qtd = st.number_input("Quantidade", min_value=1, value=1)
                    candles_pos_entrada = st.number_input("Candles após entrada", min_value=1, value=3)

                    fim_pregao = {
                        'acoes': time_obj(17, 0),
                        'mini_indice': time_obj(18, 20),
                        'mini_dolar': time_obj(18, 20)
                    }[tipo_ativo]
                    tempo_necessario = 5 * int(candles_pos_entrada)
                    ultimo_horario_entrada = (datetime.combine(datetime.today(), fim_pregao) - timedelta(minutes=tempo_necessario)).time()
                    todos_horarios_form = [f"{h:02d}:{m:02d}" for h in range(9, 19) for m in range(0, 60, 5)]
                    horarios_validos = [
                        h for h in todos_horarios_form
                        if datetime.strptime(h, '%H:%M').time() <= ultimo_horario_entrada
                    ]

                    if len(horarios_validos) < len(todos_horarios_form):
                        st.info(f"ℹ️ Com {candles_pos_entrada} candles após entrada, só horários até **{ultimo_horario_entrada.strftime('%H:%M')}** são válidos.")
                    else:
                        st.info(f"✅ Todos os horários estão disponíveis.")

                    horarios_selecionados = st.multiselect(
                        "Horários de análise",
                        options=horarios_validos,
                        default=[h for h in ["09:00", "09:05", "10:55", "11:00", "11:05"] if h in horarios_validos]
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
                            st.info("Rastreamento simulado. Função em construção.")
                        # processar_rastreamento_intraday(...) aqui depois

# ========================
# EXECUÇÃO
# ========================
if __name__ == "__main__":
    sistema_principal()
