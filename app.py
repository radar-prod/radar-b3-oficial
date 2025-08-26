# app.py
import streamlit as st
# ================
# OCULTAR BOTOES PADRÃO DO STREAMLIT
# ================
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}  /* Esconde menu superior */
footer {visibility: hidden;}     /* Esconde rodapé */
.stDeployButton {display: none;} /* Esconde botão "Deploy" */
.viewerBadge_container {display: none !important;} /* Esconde selo do GitHub */
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
import pandas as pd
import numpy as np
from datetime import datetime, time as time_obj, timedelta
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os

# ========================
# ARQUIVOS DE CONTROLE
# ========================
ARQUIVO_ACESSOS = "acessos.json"
ARQUIVO_PENDENTES = "pendentes.json"

# ========================
# FUNÇÕES DE ACESSO
# ========================
def carregar_acessos():
    if os.path.exists(ARQUIVO_ACESSOS):
        try:
            with open(ARQUIVO_ACESSOS, "r", encoding="utf-8") as f:
                dados = json.load(f)
            return dados if isinstance(dados, dict) else {}
        except Exception:
            st.error("⚠️ Arquivo corrompido. Criando novo.")
            return {}
    return {}

def verificar_acesso(email, senha):
    acessos = carregar_acessos()
    if email not in acessos:
        return False
    info = acessos[email]
    if info["senha"] != senha:
        return False
    if info["status"] != "ativo":
        return False
    expira = datetime.strptime(info["expira_em"], "%Y-%m-%d").date()
    if datetime.now().date() > expira:
        return False
    st.session_state.email = email
    st.session_state.plano = info["plano"]
    st.session_state.expira = expira
    return True

# ========================
# FUNÇÃO: SALVAR PENDENTES
# ========================
def salvar_pendentes(pendentes):
    try:
        with open(ARQUIVO_PENDENTES, "w", encoding="utf-8") as f:
            json.dump(pendentes, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"❌ Erro ao salvar pendentes: {e}")

def carregar_pendentes():
    if os.path.exists(ARQUIVO_PENDENTES):
        try:
            with open(ARQUIVO_PENDENTES, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

# ========================
# BARRA LATERAL (LOGIN E ACESSO)
# ========================
with st.sidebar:
    st.markdown("### 🔐 Acesso Exclusivo")
    email_input = st.text_input("📧 Email", key="sidebar_email")
    senha_input = st.text_input("🔑 Senha", type="password", key="sidebar_senha")

    if st.button("Entrar"):
        if verificar_acesso(email_input, senha_input):
            st.success("✅ Login realizado!")
            st.rerun()
        else:
            st.error("❌ Email ou senha inválidos")

    st.markdown("---")
    st.markdown("### 🆓 Quer testar grátis?")
    if st.button("Solicitar Acesso (15 dias)"):
        st.session_state.solicita_acesso = True
        st.rerun()

    st.markdown("---")
    st.caption("🔐 Sistema seguro. Acesso por liberação.")

# ========================
# TELA DE SOLICITAÇÃO DE ACESSO
# ========================
if "solicita_acesso" in st.session_state and st.session_state.solicita_acesso:
    st.markdown("<h1 style='text-align: center;'>🔓 Acesso Grátis por 15 Dias</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Preencha seus dados abaixo e comece a usar o <strong>Radar B3</strong> imediatamente.</p>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### 🔐 Crie seu acesso agora")
    email = st.text_input("📧 Email", key="cadastro_email")
    senha = st.text_input("🔑 Senha", type="password", key="cadastro_senha")
    confirma_senha = st.text_input("🔁 Confirmar Senha", type="password", key="cadastro_confirma")

    plano_interesse = st.selectbox(
        "🎯 Plano de interesse após o teste",
        ["Prata", "Ouro", "Diamante"]
    )

    if st.button("✅ Criar Acesso"):
        if not email or "@" not in email:
            st.error("❌ Email inválido")
        elif not senha:
            st.error("❌ Senha obrigatória")
        elif senha != confirma_senha:
            st.error("❌ As senhas não conferem")
        else:
            # Salva na lista de pendentes para o gestor liberar
            pendentes = carregar_pendentes()
            pendentes.append({
                "email": email,
                "senha": senha,
                "plano_interesse": plano_interesse,
                "data": datetime.now().strftime("%Y-%m-%d"),
                "status": "pendente",
                "dias": 15
            })
            salvar_pendentes(pendentes)

            # Mostra sucesso
            st.success(f"✅ Seu acesso foi solicitado com sucesso!")
            st.success(f"🔑 Email: {email}")
            st.info("🔍 O gestor analisará e liberará seu acesso em até 12h. Após isso, você poderá entrar com seu email e senha.")

    # ✅ BOTÃO DE VOLTAR
    if st.button("⬅️ Voltar à página inicial"):
        del st.session_state.solicita_acesso
        st.rerun()

    st.markdown("### ❓ Como funciona?")
    st.write("""
    1. Você escolhe um email e senha  
    2. Enviamos para análise  
    3. O gestor libera seu acesso por 15 dias  
    4. Você entra no sistema com suas credenciais  
    5. Após 15 dias, pode renovar ou atualizar para um plano pago
    """)

    st.stop()

# ========================
# PÁGINA INICIAL (VITRINE)
# ========================
if "email" in st.session_state and st.session_state.email:
    # Já está logado → entra no sistema
    pass
else:
    # Página inicial (vitrine)
    st.markdown("<h1 style='text-align: center;'>🎯 Radar B3 Online</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2em; font-weight: bold; color: #2c3e50;'>"
                "Padrões ocultos, resultados visíveis: a abordagem matemática para operações lucrativas"
                "</p>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### 🚀 Por que o Radar B3 faz a diferença?")
    st.write("""
    O Radar B3 não é mais um sistema de sinais. É uma **ferramenta estatística avançada** que identifica:
    - Distorções de preço com alta probabilidade de reversão ou continuidade.
    - Padrões de abertura e fechamento com taxa de acerto acima de 70%
    - Oportunidades em ações, mini-índice e mini-dólar
    """)

    # Botão "Saiba Mais"
    if st.button("📊 Saiba Mais sobre o Sistema"):
        with st.expander("🔍 Como o Radar B3 Funciona", expanded=True):
            st.markdown("""
            O Radar B3 analisa milhares de candles diários e de 5min para identificar:
            - **Distorções de preço** em relação à abertura, fechamento, mínima e máxima
            - **Padrões estatísticos** com alta taxa de acerto
            - **Entradas com risco controlado** e saídas otimizadas
            - **Drawdown Máximo** e ganho médio positivo

            ✅ Resultados comprovados  
            ✅ Testado em mais de 10 anos de dados  
            ✅ Você começa no plano grátis(15 Dias) para teste. Gostou? solicite  um upgrade através do e-mail: contatoradarb3@gmail.com
                        
            ✅ Base de dados para candles diario - Yahoo Finance(Pode divergir um pouco com os dados do Proft, mas não afeta a estatistica)
                        
            ✅ Base de dados Intraday 5min - Profit 
                        
            Nota: Resultados Passados não garantem resultados futuros                     
            """)

    # ✅ BOTÃO: PLANOS DISPONÍVEIS
    if st.button("📋 Planos Disponíveis"):
        with st.expander("💎 Planos Disponíveis", expanded=True):
            st.markdown("""
            | Recurso | Plano Bronze | Plano Prata | Plano Ouro | Plano Diamante |
            |--------|--------------|-------------|------------|----------------|
            | **Preço** | Grátis | R$ 49,90/Mês | R$ 59,90/mês | R$ 79,90/Mês |
            | **Análise Contra Tendência - Rastreamento** | Sim | Sim | Sim | Sim |
            | **Análise a Favor da Tendência - Rastreamento** | Não | Não | Sim | Sim |
            | **Qtd de ações para análise por vez** | 2 | 10 | 20 | 50 |
            | **Entrada e fechamento mesmo dia** | Sim | Sim | Sim | Sim |
            | **Entrada no dia e fechamento no dia Seguinte** | Sim | Sim | Sim | Sim |
            | **Distorções do preço com vários tipos de referência do dia anterior** | Sim | Sim | Sim | Sim |
            | **Distorção de preço customizável** | Sim | Sim | Sim | Sim |
            | **Mini Índice - Análise Intraday** | Não | Não | Não | Sim |
            | **Mini Dólar - Análise Intraday** | Não | Não | Não | Sim |
            | **Distorção do preço em relação ao preço de abertura do mercado do dia atual** | Não | Não | Não | Sim |
            | **Análise Intraday - 5min** | Não | Não | Não | Sim |
            | **Tempo Gráfico Diário** | Sim | Sim | Sim | Sim |
            | **Taxa de acerto** | Sim | Sim | Sim | Sim |
            | **Máximo Drawdown / Pior situação** | Sim | Sim | Sim | Sim |
            | **Ganho Médio por Trade** | Sim | Sim | Sim | Sim |
            | **Relatório Resumo de todos ativos** | Sim | Sim | Sim | Sim |
            | **Relatório detalhado - para validação e verificação dos trades encontrados** | Não | Sim | Sim | Sim |
            """)

    # Espaço para não colar com o footer
    st.markdown("<br><br>", unsafe_allow_html=True)

    # Rodapé
    st.markdown("---")
    st.caption("💡 Dica: Use o menu lateral para fazer login ou solicitar acesso grátis.")

# ========================
# FUNÇÕES AUXILIARES
# ========================
def extrair_nome_completo(file_name):
    return file_name.split(".")[0]

def identificar_tipo(ticker):
    ticker = ticker.upper().strip()
    if '.' in ticker:
        ticker = ticker.split('.')[0]
    for prefix in ['5-MIN_', 'MINI_', 'MIN_']:
        if ticker.startswith(prefix):
            ticker = ticker[len(prefix):]
    if 'WIN' in ticker or 'INDICE' in ticker:
        return 'mini_indice'
    if 'WDO' in ticker or 'DOLAR' in ticker or 'DOL' in ticker:
        return 'mini_dolar'
    acoes = ['PETR', 'VALE', 'ITUB', 'BBDC', 'BEEF', 'ABEV', 'ITSA', 'JBSS', 'RADL', 'CIEL', 'GOLL', 'AZUL', 'BBAS', 'SANB']
    for acao in acoes:
        if acao in ticker:
            return 'acoes'
    return 'mini_dolar'

# =====================================================
# 🔹 RASTREAMENTO INTRADAY (5min)
# =====================================================
def processar_rastreamento_intraday(
    uploaded_files,
    tipo_ativo,
    qtd,
    candles_pos_entrada,
    dist_compra_contra,
    dist_venda_contra,
    dist_favor,
    referencia,
    horarios_selecionados,
    data_inicio,
    data_fim,
    modo_estrategia
):
    todas_operacoes = []
    dias_com_entrada = set()
    dias_ignorados = []
    todos_dias_com_dados = set()

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

        for file in uploaded_files:
            try:
                ticker_nome = extrair_nome_completo(file.name)
                tipo_arquivo = identificar_tipo(ticker_nome)
                if tipo_ativo != "todos" and tipo_arquivo != tipo_ativo:
                    continue

                df = pd.read_excel(file)
                df.columns = [str(col).strip().capitalize() for col in df.columns]
                df.rename(columns={'Data': 'data', 'Abertura': 'open', 'Máxima': 'high', 'Mínima': 'low', 'Fechamento': 'close'}, inplace=True)
                df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
                df = df.dropna(subset=['data'])
                df['data_limpa'] = df['data'].dt.floor('min')
                df = df.set_index('data_limpa').sort_index()
                df = df[~df.index.duplicated(keep='first')]
                df['data_sozinha'] = df.index.date
                df = df[(df['data_sozinha'] >= data_inicio) & (df['data_sozinha'] <= data_fim)]

                if df.empty:
                    continue

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

                    idx_saida = idx_entrada + timedelta(minutes=5 * int(candles_pos_entrada))

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

                    if modo_estrategia in ["A Favor da Tendência", "Ambos"]:
                        if distorcao_percentual > dist_favor:
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
                        elif distorcao_percentual < -dist_favor:
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

            except Exception as e:
                st.write(f"❌ Erro ao processar {file.name}: {e}")
                continue

    df_ops = pd.DataFrame(todas_operacoes)
    return df_ops, list(dias_com_entrada), dias_ignorados, sorted(todos_dias_com_dados)

# =====================================================
# 🔹 RASTREAMENTO DIÁRIO
# =====================================================
def processar_rastreamento_diario(
    tickers,
    volume_minimo,
    dist_compra,
    dist_venda,
    qtd,
    referencia_tipo,
    saida_tipo,
    data_inicio,
    data_fim,
    modo_analise,
    dist_favor
):
    todas_operacoes = []
    tickers_processados = 0
    tickers_com_erro = []

    for ticker in tickers:
        try:
            ticker_clean = ticker.strip().upper().replace(".SA", "")
            if not ticker_clean:
                tickers_com_erro.append(f"{ticker} (vazio)")
                continue

            ticker_yf = ticker_clean + ".SA"
            data = pd.DataFrame()
            for _ in range(3):
                try:
                    data = yf.download(ticker_yf, start=data_inicio, end=data_fim + timedelta(days=1), progress=False)
                    if not data.empty: break
                except: pass
                try:
                    ticker_obj = yf.Ticker(ticker_yf)
                    data = ticker_obj.history(start=data_inicio, end=data_fim)
                    if not data.empty: break
                except: pass

            if data.empty:
                tickers_com_erro.append(f"{ticker_clean} (sem dados)")
                continue

            if isinstance(data.columns, pd.MultiIndex):
                data.columns = [col[0] for col in data.columns]
            data.columns = [col.capitalize() for col in data.columns]

            required = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required:
                if col not in data.columns:
                    tickers_com_erro.append(f"{ticker_clean} (falta {col})")
                    continue

            for col in required:
                data[col] = pd.to_numeric(data[col], errors='coerce')
            data.dropna(subset=required, inplace=True)
            if len(data) < 2:
                tickers_com_erro.append(f"{ticker_clean} (poucos dados)")
                continue

            data['Volume_Reais'] = data['Volume'] * data['Close']
            volume_medio = data['Volume_Reais'].tail(21).mean()
            if pd.isna(volume_medio) or volume_medio < volume_minimo:
                tickers_com_erro.append(f"{ticker_clean} (volume baixo: R$ {volume_medio:,.0f})")
                continue

            data = data.loc[str(data_inicio):str(data_fim)]
            if len(data) < 2:
                tickers_com_erro.append(f"{ticker_clean} (sem dados no período)")
                continue

            operacoes = []
            for i in range(1, len(data)):
                row_atual = data.iloc[i]
                row_anterior = data.iloc[i-1]

                try:
                    if referencia_tipo == "Fechamento do dia anterior":
                        ref = float(row_anterior['Close'])
                    elif referencia_tipo == "Abertura do dia anterior":
                        ref = float(row_anterior['Open'])
                    elif referencia_tipo == "Mínima do dia anterior":
                        ref = float(row_anterior['Low'])
                    elif referencia_tipo == "Máxima do dia anterior":
                        ref = float(row_anterior['High'])
                    else:
                        continue
                    if pd.isna(ref) or not np.isfinite(ref):
                        continue
                except:
                    continue

                low_atual = float(row_atual['Low'])
                high_atual = float(row_atual['High'])
                open_atual = float(row_atual['Open'])

                preco_alvo_compra = ref * (1 - dist_compra / 100)
                preco_alvo_venda = ref * (1 + dist_venda / 100)

                if modo_analise in ["Contra Tendência", "Ambos"]:
                    if low_atual <= preco_alvo_compra and i+1 < len(data):
                        preco_entrada = open_atual if open_atual < preco_alvo_compra else preco_alvo_compra
                        preco_saida = float(data.iloc[i+1]['Open']) if saida_tipo == "Abertura do dia seguinte" else float(row_atual['Close'])
                        lucro_reais = (preco_saida - preco_entrada) * qtd
                        max_dd_percent = ((low_atual - preco_entrada) / preco_entrada) * 100

                        operacoes.append({
                            "Ação": ticker_clean,
                            "Direção": "Compra (Contra)",
                            "Data Entrada": str(data.index[i].date()),
                            "Data Saída": str(data.index[i+1].date()) if saida_tipo == "Abertura do dia seguinte" else str(data.index[i].date()),
                            "Preço Entrada": round(preco_entrada, 2),
                            "Preço Saída": round(preco_saida, 2),
                            "Lucro (R$)": round(lucro_reais, 2),
                            "Distorção (%)": f"-{dist_compra:.2f}%",
                            "Quantidade": qtd,
                            "Referência": f"{referencia_tipo}: {ref:.2f}",
                            "Max Drawdown %": round(max_dd_percent, 2)
                        })

                    if high_atual >= preco_alvo_venda and i+1 < len(data):
                        preco_entrada = open_atual if open_atual > preco_alvo_venda else preco_alvo_venda
                        preco_saida = float(data.iloc[i+1]['Open']) if saida_tipo == "Abertura do dia seguinte" else float(row_atual['Close'])
                        lucro_reais = (preco_entrada - preco_saida) * qtd
                        max_dd_percent = ((high_atual - preco_entrada) / preco_entrada) * 100

                        operacoes.append({
                            "Ação": ticker_clean,
                            "Direção": "Venda (Contra)",
                            "Data Entrada": str(data.index[i].date()),
                            "Data Saída": str(data.index[i+1].date()) if saida_tipo == "Abertura do dia seguinte" else str(data.index[i].date()),
                            "Preço Entrada": round(preco_entrada, 2),
                            "Preço Saída": round(preco_saida, 2),
                            "Lucro (R$)": round(lucro_reais, 2),
                            "Distorção (%)": f"+{dist_venda:.2f}%",
                            "Quantidade": qtd,
                            "Referência": f"{referencia_tipo}: {ref:.2f}",
                            "Max Drawdown %": round(max_dd_percent, 2)
                        })

                if modo_analise in ["A Favor da Tendência", "Ambos"]:
                    ref = float(row_anterior['Close'])
                    preco_alvo_compra = ref * (1 - dist_favor / 100)
                    preco_alvo_venda = ref * (1 + dist_favor / 100)

                    if high_atual >= preco_alvo_venda and i+1 < len(data):
                        preco_entrada = open_atual if open_atual > preco_alvo_venda else preco_alvo_venda
                        preco_saida = float(data.iloc[i+1]['Open']) if saida_tipo == "Abertura do dia seguinte" else float(row_atual['Close'])
                        lucro_reais = (preco_entrada - preco_saida) * qtd

                        close_dia_entrada = row_atual['Close']
                        if close_dia_entrada > preco_entrada:
                            max_dd_percent = ((close_dia_entrada - preco_entrada) / preco_entrada) * 100
                        else:
                            max_dd_percent = 0.0

                        operacoes.append({
                            "Ação": ticker_clean,
                            "Direção": "Venda (Favor)",
                            "Data Entrada": str(data.index[i].date()),
                            "Data Saída": str(data.index[i+1].date()) if saida_tipo == "Abertura do dia seguinte" else str(data.index[i].date()),
                            "Preço Entrada": round(preco_entrada, 2),
                            "Preço Saída": round(preco_saida, 2),
                            "Lucro (R$)": round(lucro_reais, 2),
                            "Distorção (%)": f"+{dist_favor:.2f}%",
                            "Quantidade": qtd,
                            "Referência": f"Alvo +{dist_favor}%: {ref:.2f}",
                            "Max Drawdown %": round(max_dd_percent, 2)
                        })

                    elif low_atual <= preco_alvo_compra and i+1 < len(data):
                        preco_entrada = open_atual if open_atual < preco_alvo_compra else preco_alvo_compra
                        preco_saida = float(data.iloc[i+1]['Open']) if saida_tipo == "Abertura do dia seguinte" else float(row_atual['Close'])
                        lucro_reais = (preco_saida - preco_entrada) * qtd

                        close_dia_entrada = row_atual['Close']
                        if close_dia_entrada < preco_entrada:
                            max_dd_percent = ((close_dia_entrada - preco_entrada) / preco_entrada) * 100
                        else:
                            max_dd_percent = 0.0

                        operacoes.append({
                            "Ação": ticker_clean,
                            "Direção": "Compra (Favor)",
                            "Data Entrada": str(data.index[i].date()),
                            "Data Saída": str(data.index[i+1].date()) if saida_tipo == "Abertura do dia seguinte" else str(data.index[i].date()),
                            "Preço Entrada": round(preco_entrada, 2),
                            "Preço Saída": round(preco_saida, 2),
                            "Lucro (R$)": round(lucro_reais, 2),
                            "Distorção (%)": f"-{dist_favor:.2f}%",
                            "Quantidade": qtd,
                            "Referência": f"Alvo -{dist_favor}%: {ref:.2f}",
                            "Max Drawdown %": round(max_dd_percent, 2)
                        })

            todas_operacoes.extend(operacoes)
            tickers_processados += 1

        except Exception as e:
            tickers_com_erro.append(f"{ticker} ({str(e)})")
            continue

    df_ops = pd.DataFrame(todas_operacoes)
    return df_ops, tickers_com_erro

# ========================
# SELETOR DE MODO POR PLANO
# ========================
def sistema_principal():
    st.success("✅ Acesso liberado")
    st.write(f"📆 Expira em: **{st.session_state.expira.strftime('%d/%m/%Y')}**")
    st.markdown(f"Olá, **{st.session_state.email}**! Bem-vindo ao Radar B3.")
    # 🔐 Botão para baixar pendentes.json (apenas para admin)
    EMAIL_ADMIN = "oliveiradmso@gmail.com"  # 👈 Substitua por seu email de confiança

    if st.session_state.email == EMAIL_ADMIN:
        st.markdown("---")
        st.markdown("### 🔐 Acesso do Administrador")

        if st.button("📥 Baixar pendentes.json (para sincronizar com o gestor)"):
            try:
                with open("pendentes.json", "r", encoding="utf-8") as f:
                    data = f.read()
                st.download_button(
                    label="⬇️ Clique para baixar o arquivo pendentes.json",
                    data=data,
                    file_name="pendentes.json",
                    mime="application/json",
                    key="download_pendentes"
                )
            except FileNotFoundError:
                st.error("❌ Arquivo pendentes.json não encontrado no servidor.")
            except Exception as e:
                st.error(f"❌ Erro ao ler o arquivo: {e}")

    # ✅ Agora usa os nomes amigáveis diretamente

    plano = st.session_state.plano

    # ✅ Agora usa os nomes amigáveis diretamente
    if plano == "Bronze":
        st.markdown("### ⚪ Plano Bronze")
        modo_sistema = st.selectbox("", ["Plano Bronze"])
        modo_analise = st.radio("Modo de Análise", ["Contra Tendência"])
        limite_ativos = 2
        relatorio_detalhado = False
        intraday = False
        abertura_dia_atual = False

    elif plano == "Prata":
        st.markdown("### ⚪ Plano Prata")
        modo_sistema = st.selectbox("", ["Plano Prata"])
        modo_analise = st.radio("Modo de Análise", ["Contra Tendência"])
        limite_ativos = 10
        relatorio_detalhado = True
        intraday = False
        abertura_dia_atual = False

    elif plano == "Ouro":
        st.markdown("### 🟨 Ouro")
        modo_sistema = st.selectbox("", ["Plano Ouro"])
        modo_analise = st.radio("Modo de Análise", ["Contra Tendência", "A Favor da Tendência", "Ambos"])
        limite_ativos = 20
        relatorio_detalhado = True
        intraday = False
        abertura_dia_atual = False

    elif plano == "Diamante":
        st.markdown("### 💎 Diamante")
        modo_sistema = st.selectbox("", ["Diamante - Diário", "Diamante - Intraday"])
        modo_analise = st.radio("Modo de Análise", ["Contra Tendência", "A Favor da Tendência", "Ambos"])
        limite_ativos = 50
        relatorio_detalhado = True
        intraday = True
        abertura_dia_atual = True

    else:
        st.error("❌ Plano inválido ou desconhecido.")
        st.stop()

    # ============ MODO DIÁRIO ============
    if modo_sistema in ["Plano Bronze", "Plano Prata", "Plano Ouro", "Diamante - Diário"]:
        st.header("📅 Configurações do Rastreamento Diário")

        volume_minimo_opcoes = {
            "25 mil": 25_000,
            "50 mil": 50_000,
            "100 mil": 100_000,
            "200 mil": 200_000,
            "300 mil": 300_000,
            "400 mil": 400_000,
            "500 mil": 500_000,
            "1 milhão": 1_000_000,
            "2 milhões": 2_000_000
        }
        volume_minimo_nome = st.selectbox("Volume médio mínimo diário", list(volume_minimo_opcoes.keys()))
        volume_minimo = volume_minimo_opcoes[volume_minimo_nome]

        ativos_diarios = st.text_input(f"Ativos (até {limite_ativos})", value="PETR4, VALE3, ITUB4, BBDC4")
        tickers_input = [t.strip() for t in ativos_diarios.split(",") if t.strip()]
        tickers = tickers_input[:limite_ativos]
        num_inseridas = len(tickers)
        st.info(f"📌 {num_inseridas} ações inseridas.")

        col1, col2 = st.columns(2)
        with col1:
            dist_compra = st.number_input("Distorção mínima para COMPRA (%) - Contra", value=3.0, min_value=0.1)
        with col2:
            dist_venda = st.number_input("Distorção mínima para VENDA (%) - Contra", value=3.0, min_value=0.1)

        qtd = st.number_input("Quantidade", min_value=1, value=1, help="Ex: 100 para ações, 1 para mini")

        referencia_tipo = st.selectbox(
            "Referência",
            ["Fechamento do dia anterior", "Abertura do dia anterior", "Mínima do dia anterior", "Máxima do dia anterior"]
        )
        if plano == "Diamante":
            referencia_tipo = st.selectbox(
                "Referência",
                ["Fechamento do dia anterior", "Abertura do dia anterior", "Mínima do dia anterior", "Máxima do dia anterior", "Abertura do dia atual"]
            )

        saida_tipo = st.selectbox(
            "Saída",
            ["Fechamento do dia", "Abertura do dia seguinte"]
        )

        data_inicio_diario = st.date_input("Data Início", value=datetime(2020, 1, 1))
        data_fim_diario = st.date_input("Data Fim", value=datetime.today().date())

        if plano in ["Ouro", "Diamante"]:
            dist_favor = st.number_input("Distorção mínima A FAVOR da tendência (%)", value=2.0, min_value=0.1)
        else:
            dist_favor = 2.0

        if st.button("🔍 Iniciar Rastreamento"):
            st.cache_data.clear()
            if "todas_operacoes_diarias" in st.session_state:
                del st.session_state.todas_operacoes_diarias
            if "df_ops" in st.session_state:
                del st.session_state.df_ops

            df_ops, tickers_com_erro = processar_rastreamento_diario(
                tickers=tickers,
                volume_minimo=volume_minimo,
                dist_compra=dist_compra,
                dist_venda=dist_venda,
                qtd=qtd,
                referencia_tipo=referencia_tipo,
                saida_tipo=saida_tipo,
                data_inicio=data_inicio_diario,
                data_fim=data_fim_diario,
                modo_analise=modo_analise,
                dist_favor=dist_favor
            )

            if tickers_com_erro:
                st.info(f"📊 {len(tickers_com_erro)} ações não foram analisadas porque não têm volume ou dados suficientes.")
                with st.expander("📋 Ver ações excluídas"):
                    for erro in tickers_com_erro:
                        st.write(f"🔹 {erro}")

            st.success(f"✅ {len(tickers)} ações processadas com sucesso.")

            if df_ops.empty:
                st.warning("❌ Nenhuma oportunidade foi detectada.")
            else:
                for col in ['Preço Entrada', 'Preço Saída', 'Lucro (R$)', 'Max Drawdown %']:
                    if col in df_ops.columns and df_ops[col].dtype == 'object':
                        df_ops[col] = pd.to_numeric(df_ops[col].astype(str).str.replace(',', '.'), errors='coerce')

                resumo = df_ops.groupby(['Ação', 'Direção']).agg(
                    Total_Eventos=('Lucro (R$)', 'count'),
                    Acertos=('Lucro (R$)', lambda x: (x > 0).sum()),
                    Lucro_Total=('Lucro (R$)', 'sum'),
                    Max_DD_Medio_Percent=('Max Drawdown %', 'mean')
                ).reset_index()

                resumo['Taxa de Acerto'] = (resumo['Acertos'] / resumo['Total_Eventos']).map(lambda x: f"{x:.2%}")
                resumo['Lucro Total (R$)'] = "R$ " + resumo['Lucro_Total'].map(lambda x: f"{x:.2f}")
                resumo['Ganho Médio por Trade (R$)'] = (resumo['Lucro_Total'] / resumo['Total_Eventos']).map(lambda x: f"R$ {x:+.2f}")
                resumo['Máx. Drawdown Médio (%)'] = resumo['Max_DD_Medio_Percent'].map(lambda x: f"{x:+.2f}%")

                st.markdown("### 📊 Resumo Consolidado por Ação e Direção")
                st.dataframe(
                    resumo[[
                        'Ação', 'Direção', 'Total_Eventos', 'Acertos', 'Taxa de Acerto',
                        'Lucro Total (R$)', 'Ganho Médio por Trade (R$)', 'Máx. Drawdown Médio (%)'
                    ]],
                    use_container_width=True
                )

                if plano != "Bronze":
                    csv_data = df_ops.to_csv(index=False, sep=";", decimal=",", encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Exportar Resultados para CSV",
                        data=csv_data,
                        file_name="resultados_radar_b3.csv",
                        mime="text/csv"
                    )

                if plano in ["Prata", "Ouro", "Diamante"]:
                    with st.expander("🔍 Ver oportunidades detalhadas"):
                        st.dataframe(df_ops, use_container_width=True)
                else:
                    st.info("🔒 Relatório detalhado disponível a partir do Plano Prata. Atualize para ver cada trade encontrado.")

                st.markdown("---")
                st.markdown("""
                <div style="background-color: #f0f8ff; padding: 20px; border-radius: 10px; border: 1px solid #bee1ff; text-align: center;">
                    <h3>Quer rastrear até 50 ações ao mesmo tempo?</h3>
                    <p><strong>Libere todo o poder do Radar B3</strong>: análise intraday, WIN, WDO, múltiplas estratégias e rastreamento em massa.</p>
                    <p><strong>Contra Tendência</strong> e <strong>A Favor da Tendência</strong> disponíveis no plano <strong>DIAMANTE</strong>.</p>
                </div>
                """, unsafe_allow_html=True)

                # ✅ BOTÃO DE UPGRADE (aparece para Bronze, Prata e Ouro)
                if plano in ["Bronze", "Prata", "Ouro"]:
                    st.markdown("---")
                    st.markdown("""
                    ### 💎 Quer mais recursos?
                    Atualize seu plano e libere funcionalidades exclusivas:
                    - **Análise Intraday (5min)**
                    - **Rastreamento em WIN e WDO**
                    - **Estratégia a favor da tendência**
                    - **Distorção em relação à abertura do dia atual**
                    - **Até 50 ativos simultâneos**

                    📲 Entre em contato para fazer upgrade!
                    """)
                    st.info("💬 Envie um e-mail para contatoradarb3@gmail.com  para atualizar seu plano.")

    # ============ MODO INTRADAY ============
    elif modo_sistema == "Diamante - Intraday":
        if plano != "Diamante":
            st.error("❌ Acesso ao modo Intraday é exclusivo para o Plano Diamante.")
            st.stop()

        st.header("📤 Carregue seus Dados (Excel 5min)")
        uploaded_files = st.file_uploader("Escolha um ou mais arquivos .xlsx", type=["xlsx"], accept_multiple_files=True)

        if uploaded_files:
            limites_por_plano = {
                "Bronze": 2,
                "Prata": 6,
                "Ouro": 12,
                "Diamante": 9999
            }
            limite = limites_por_plano.get(st.session_state.plano, 2)
            if len(uploaded_files) > limite:
                st.error(f"❌ Seu plano permite {limite} arquivos. Você enviou {len(uploaded_files)}.")
                st.stop()
            else:
                st.info(f"📌 Seu plano permite até {limite} arquivos. ({len(uploaded_files)} enviados)")

            st.info(f"✅ {len(uploaded_files)} arquivo(s) carregado(s).")

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
                    if plano == "Ouro" and tipo_ativo in ["mini_indice", "mini_dolar"]:
                        st.warning("⚠️ No plano Ouro, só é permitido analisar ações.")
                        tipo_ativo = "acoes"

                    todos_horarios = [f"{h:02d}:{m:02d}" for h in range(9, 19) for m in range(0, 60, 5)]
                    horarios_selecionados = st.multiselect(
                        "Horários de análise",
                        todos_horarios,
                        default=["09:00"]
                    )

                    qtd = st.number_input("Quantidade", min_value=1, value=1)
                    candles_pos_entrada = st.number_input("Candles após entrada", min_value=1, value=3)

                    modo_estrategia = st.selectbox(
                        "Modo da Estratégia",
                        ["Contra Tendência", "A Favor da Tendência", "Ambos"]
                    )

                    if modo_estrategia in ["Contra Tendência", "Ambos"]:
                        dist_compra_contra = st.number_input("Distorção mínima COMPRA (%) - Contra", value=0.3)
                        dist_venda_contra = st.number_input("Distorção mínima VENDA (%) - Contra", value=0.3)
                    else:
                        dist_compra_contra = dist_venda_contra = 0.0

                    if modo_estrategia in ["A Favor da Tendência", "Ambos"]:
                        dist_favor = st.number_input("Distorção mínima A FAVOR da tendência (%)", value=0.5)
                    else:
                        dist_favor = 0.0

                    referencia = st.selectbox(
                        "Referência da distorção",
                        ["Fechamento do dia anterior", "Mínima do dia anterior", "Abertura do dia atual"]
                    )

                    submitted = st.form_submit_button("✅ Aplicar Configurações")

                if submitted:
                    horarios_validos = []
                    horarios_invalidos = []
                    for horario in horarios_selecionados:
                        h, m = map(int, horario.split(":"))
                        hora = time_obj(h, m)
                        if tipo_ativo == "acoes":
                            if time_obj(10, 0) <= hora <= time_obj(17, 0):
                                horarios_validos.append(horario)
                            else:
                                horarios_invalidos.append(horario)
                        else:
                            if time_obj(9, 0) <= hora <= time_obj(18, 20):
                                horarios_validos.append(horario)
                            else:
                                horarios_invalidos.append(horario)

                    if horarios_invalidos:
                        st.error(f"""
                        ❌ Horários inválidos para {tipo_ativo.replace('_', ' ').title()}:
                        - {', '.join(horarios_invalidos)}
                        """)
                    elif not horarios_validos:
                        st.warning("⚠️ Nenhum horário válido foi selecionado.")
                    else:
                        st.session_state.configuracoes_salvas = {
                            "tipo_ativo": tipo_ativo,
                            "qtd": qtd,
                            "candles_pos_entrada": candles_pos_entrada,
                            "dist_compra_contra": dist_compra_contra,
                            "dist_venda_contra": dist_venda_contra,
                            "dist_favor": dist_favor,
                            "referencia": referencia,
                            "horarios_selecionados": horarios_validos,
                            "modo_estrategia": modo_estrategia
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
                                dist_favor=cfg["dist_favor"],
                                referencia=cfg["referencia"],
                                horarios_selecionados=cfg["horarios_selecionados"],
                                data_inicio=data_inicio,
                                data_fim=data_fim,
                                modo_estrategia=cfg["modo_estrategia"]
                            )

                        if not df_ops.empty:
                            df_ops = df_ops[df_ops['Horário'].isin(cfg["horarios_selecionados"])].copy()
                            st.session_state.todas_operacoes = df_ops
                            st.success(f"✅ Rastreamento concluído: {len(df_ops)} oportunidades detectadas.")

                            for col in ['Preço Entrada', 'Preço Saída', 'Lucro (R$)', 'Max Drawdown %']:
                                if col in df_ops.columns and df_ops[col].dtype == 'object':
                                    df_ops[col] = pd.to_numeric(df_ops[col].astype(str).str.replace(',', '.'), errors='coerce')

                            resumo = df_ops.groupby(['Ação', 'Direção']).agg(
                                Total_Eventos=('Lucro (R$)', 'count'),
                                Acertos=('Lucro (R$)', lambda x: (x > 0).sum()),
                                Lucro_Total=('Lucro (R$)', 'sum'),
                                Max_DD_Medio_Percent=('Max Drawdown %', 'mean')
                            ).reset_index()

                            resumo['Taxa de Acerto'] = (resumo['Acertos'] / resumo['Total_Eventos']).map(lambda x: f"{x:.2%}")
                            resumo['Lucro Total (R$)'] = "R$ " + resumo['Lucro_Total'].map(lambda x: f"{x:.2f}")
                            resumo['Ganho Médio por Trade (R$)'] = (resumo['Lucro_Total'] / resumo['Total_Eventos']).map(lambda x: f"R$ {x:+.2f}")
                            resumo['Máx. Drawdown Médio (%)'] = resumo['Max_DD_Medio_Percent'].map(lambda x: f"{x:+.2f}%")

                            st.markdown("### 📊 Resumo Consolidado por Ação e Direção")
                            st.dataframe(
                                resumo[[
                                    'Ação', 'Direção', 'Total_Eventos', 'Acertos', 'Taxa de Acerto',
                                    'Lucro Total (R$)', 'Ganho Médio por Trade (R$)', 'Máx. Drawdown Médio (%)'
                                ]],
                                use_container_width=True
                            )

                            csv_data = df_ops.to_csv(index=False, sep=";", decimal=",", encoding='utf-8-sig')
                            st.download_button(
                                label="📥 Exportar Resultados para CSV",
                                data=csv_data,
                                file_name="resultados_intraday.csv",
                                mime="text/csv"
                            )

                        else:
                            st.warning("❌ Nenhuma oportunidade foi detectada.")

                        with st.expander("📊 Análise de Dias"):
                            st.write("Dias com entrada e saída válida:", len(dias_com_entrada))
                            if dias_ignorados:
                                st.write("Dias ignorados:")
                                for dia, motivo in dias_ignorados[:10]:
                                    st.write(f"- {dia.strftime('%d/%m')} → {motivo}")

                        if not df_ops.empty:
                            df_detalhe = df_ops.copy()
                            df_detalhe['Lucro (R$)'] = pd.to_numeric(df_detalhe['Lucro (R$)'], errors='coerce')
                            df_detalhe['Acerto?'] = df_detalhe['Lucro (R$)'].apply(
                                lambda x: '✅ Sim' if x > 0 else '❌ Não' if x < 0 else '➖ Neutro'
                            )
                            cols = df_detalhe.columns.tolist()
                            lucro_idx = cols.index('Lucro (R$)')
                            cols.insert(lucro_idx + 1, cols.pop(cols.index('Acerto?')))
                            df_detalhe = df_detalhe[cols]

                            def colorir_linhas(row):
                                valor = row['Lucro (R$)']
                                if valor > 0:
                                    return ['background-color: #d4edda'] * len(row)
                                elif valor < 0:
                                    return ['background-color: #f8d7da'] * len(row)
                                else:
                                    return ['background-color: #fff3cd'] * len(row)

                            with st.expander("🔍 Ver oportunidades detalhadas (Intraday)"):
                                st.dataframe(
                                    df_detalhe.style.apply(colorir_linhas, axis=1),
                                    use_container_width=True
                                )

# ========================
# FLUXO PRINCIPAL
# ========================
if "email" in st.session_state and st.session_state.email:
    sistema_principal()
else:
    # A vitrine já foi exibida acima
    pass
