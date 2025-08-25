# gestor.py
import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pandas as pd

# ========================
# CONFIGURAÇÃO
# ========================
ARQUIVO = "acessos.json"
PENDENTES_FILE = "pendentes.json"
BACKUP_DIR = "backups"

if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

# ========================
# FUNÇÕES
# ========================
def carregar_acessos():
    if os.path.exists(ARQUIVO):
        try:
            with open(ARQUIVO, "r", encoding="utf-8") as f:
                dados = json.load(f)
            return dados if isinstance(dados, dict) else {}
        except Exception as e:
            st.error(f"⚠️ Erro ao ler {ARQUIVO}: {e}")
            return {}
    return {}

def salvar_acessos(dados):
    try:
        with open(ARQUIVO, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        st.success("✅ Dados salvos com sucesso.")
    except Exception as e:
        st.error(f"❌ Erro ao salvar {ARQUIVO}: {e}")

def carregar_pendentes():
    if os.path.exists(PENDENTES_FILE):
        try:
            with open(PENDENTES_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)
            return [p for p in dados if isinstance(p, dict)]
        except Exception:
            st.error("⚠️ Arquivo pendentes.json corrompido.")
            return []
    return []

def salvar_pendentes(dados):
    try:
        with open(PENDENTES_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"❌ Erro ao salvar pendentes: {e}")

def expirar_todos(dados):
    hoje = datetime.now().date()
    for email, info in dados.items():
        if isinstance(info, dict):
            expira_str = info.get("expira_em", "")
            if expira_str:
                try:
                    expira = datetime.strptime(expira_str, "%Y-%m-%d").date()
                    if hoje > expira and info.get("status") == "ativo":
                        info["status"] = "expirado"
                except:
                    continue
    return dados

def gerar_backup():
    dados = carregar_acessos()
    if not dados:
        return None

    linhas = []
    for email, info in dados.items():
        if isinstance(info, dict):
            linhas.append({
                "Email": email,
                "Senha": info.get("senha", "") or "",
                "Plano": info.get("plano", ""),
                "Liberado em": info.get("liberado_em", ""),
                "Expira em": info.get("expira_em", ""),
                "Status": info.get("status", "").capitalize()
            })
    df = pd.DataFrame(linhas)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    nome_arquivo = f"backup_clientes_{timestamp}.xlsx"
    caminho = os.path.join(BACKUP_DIR, nome_arquivo)

    try:
        df.to_excel(caminho, index=False, sheet_name="Clientes")
        st.session_state.ultimo_backup = datetime.now().strftime("%d/%m/%Y às %H:%M")
        return caminho
    except Exception as e:
        st.error(f"❌ Erro ao salvar backup: {e}")
        return None

# ========================
# CARREGAR DADOS
# ========================
dados = carregar_acessos()
pendentes = carregar_pendentes()
dados = expirar_todos(dados)
salvar_acessos(dados)

# Inicializa variáveis de sessão
if "ultimo_backup" not in st.session_state:
    st.session_state.ultimo_backup = "Nenhum backup ainda"

# ========================
# CONTAGEM DE CLIENTES E PENDENTES
# ========================
ativos = 0
expirados = 0
for info in dados.values():
    if not isinstance(info, dict):
        continue
    if info.get("status") == "ativo":
        ativos += 1
    elif info.get("status") == "expirado":
        expirados += 1

qtd_pendentes = len(pendentes)

# ========================
# INTERFACE PRINCIPAL
# ========================
st.markdown("<h1 style='text-align: center;'>🔐 Gestor de Acesso</h1>", unsafe_allow_html=True)
st.markdown("---")

# ✅ Painel com 4 métricas
col1, col2, col3, col4 = st.columns(4)
col1.metric("✅ Ativos", ativos)
col2.metric("🔴 Expirados", expirados)
col3.metric("⏳ Pendentes", qtd_pendentes)
col4.metric("🔁 Último Backup", st.session_state.ultimo_backup)

# ========================
# BOTÃO DE BACKUP
# ========================
if st.button("📥 Gerar Backup em Excel"):
    caminho = gerar_backup()
    if caminho:
        with open(caminho, "rb") as f:
            st.download_button(
                label="💾 Baixar Backup Excel",
                data=f.read(),
                file_name=os.path.basename(caminho),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"backup_{datetime.now().timestamp()}"
            )

# ========================
# ABAS
# ========================
aba = st.tabs(["📋 Clientes", "⏳ Pendentes", "➕ Cadastrar Manual", "🔔 Avisar e Renovar"])

# --- ABAS ---
with aba[0]:
    st.subheader("Clientes Ativos e Expirados")

    if not dados:
        st.info("Nenhum cliente cadastrado.")
    else:
        # Cria DataFrame com os dados
        df_clientes = pd.DataFrame([
            {
                "Email": email,
                "Senha": info.get("senha", ""),
                "Plano": info.get("plano", ""),
                "Liberado em": info.get("liberado_em", ""),
                "Expira em": info.get("expira_em", ""),
                "Status": info.get("status", "").capitalize()
            }
            for email, info in dados.items() if isinstance(info, dict)
        ])

        # Ordena por status
        df_clientes = df_clientes.sort_values(by="Status", ascending=False)

        # Exibe tabela
        st.data_editor(
            df_clientes,
            column_config={
                "Senha": st.column_config.TextColumn("Senha", width="medium")
            },
            hide_index=True,
            use_container_width=True
        )

    # === Botão de exclusão (com confirmação) ===
    emails = list(dados.keys())
    if emails:
        email_para_excluir = st.selectbox("🗑️ Selecionar cliente para excluir", [""] + emails)
        if email_para_excluir:
            st.warning(f"⚠️ Deletar permanentemente **{email_para_excluir}**?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Sim, deletar", key=f"conf_delete_{email_para_excluir}"):
                    del dados[email_para_excluir]
                    salvar_acessos(dados)
                    st.success(f"✅ {email_para_excluir} removido.")
                    st.rerun()
            with col2:
                if st.button("❌ Cancelar", key=f"cancel_delete_{email_para_excluir}"):
                    st.rerun()

    # Atualizar status
    if st.button("🔄 Atualizar status (expirados)"):
        dados_atualizados = expirar_todos(dados)
        salvar_acessos(dados_atualizados)
        st.rerun()

# --- ABAS ---
with aba[1]:
    st.subheader("Solicitações de Teste Grátis")

    if not pendentes:
        st.info("Nenhuma solicitação recebida.")
    else:
        for i, p in enumerate(pendentes):
            email = p.get("email", "Sem email")
            senha = p.get("senha", "n/a")
            plano = p.get("plano_interesse", "n/a")
            data = p.get("data", "n/a")

            cols = st.columns([3, 2, 2, 2, 1])
            cols[0].write(email)
            cols[1].write(senha)
            cols[2].write(plano)
            cols[3].write(data)
            if cols[4].button("✅ Liberar", key=f"lib_{i}"):
                if not senha:
                    st.error("❌ Cliente não definiu senha.")
                else:
                    expira = (datetime.now().date() + timedelta(days=15)).strftime("%Y-%m-%d")
                    dados[email] = {
                        "senha": senha,
                        "plano": "Bronze",
                        "liberado_em": datetime.now().strftime("%Y-%m-%d"),
                        "expira_em": expira,
                        "status": "ativo"
                    }
                    pendentes.pop(i)
                    salvar_acessos(dados)
                    salvar_pendentes(pendentes)
                    st.success(f"✅ {email} liberado com plano Bronze por 15 dias.")
                    st.rerun()

# --- ABAS ---
with aba[2]:
    st.subheader("➕ Cadastrar Cliente Manualmente")
    with st.form("cadastrar"):
        email = st.text_input("📧 Email do cliente")
        senha = st.text_input("🔑 Senha", type="password")
        plano = st.selectbox("🎯 Plano", ["Bronze", "Prata", "Ouro", "Diamante"])
        dias = st.number_input("📅 Dias de acesso", min_value=1, value=30)
        
        if st.form_submit_button("✅ Salvar / Renovar"):
            if not email or "@" not in email:
                st.error("❌ Email inválido")
            elif not senha:
                st.error("❌ Senha obrigatória")
            else:
                expira = (datetime.now().date() + timedelta(days=dias)).strftime("%Y-%m-%d")
                dados[email] = {
                    "senha": senha,
                    "plano": plano,
                    "liberado_em": datetime.now().strftime("%Y-%m-%d"),
                    "expira_em": expira,
                    "status": "ativo"
                }
                salvar_acessos(dados)
                st.success(f"✅ {email} foi liberado até {expira}")
                st.rerun()

# --- ABAS ---
with aba[3]:
    st.subheader("🔔 Avisar e Renovar")

    hoje = datetime.now().date()

    # Listas
    proximos_3dias = []
    proximos_1dia = []
    expirados = []

    for email, info in dados.items():
        if not isinstance(info, dict):
            continue
        expira_str = info.get("expira_em", "")
        if not expira_str:
            continue
        try:
            expira = datetime.strptime(expira_str, "%Y-%m-%d").date()
            dias_restantes = (expira - hoje).days

            if dias_restantes == 3:
                proximos_3dias.append((email, info))
            elif dias_restantes == 1:
                proximos_1dia.append((email, info))
            elif dias_restantes < 0:
                expirados.append((email, info))
        except:
            continue

    # === Avisos ===
    if proximos_3dias:
        st.markdown("### 🟡 Expiram em 3 dias")
        for email, info in proximos_3dias:
            plano = info.get("plano", "n/a")
            assunto = "Seu acesso ao Radar B3 expira em 3 dias"
            mensagem = (
                f"Olá!\n\n"
                f"Seu acesso ao Radar B3 expira em 3 dias.\n"
                f"Renove agora para continuar com análises de intraday, distorção de preço e padrões lucrativos.\n\n"
                f"Link de renovação: https://seusite.com/renovar\n\n"
                f"Abraços,\n"
                f"Time Radar B3"
            )
            mensagem_encoded = mensagem.replace(' ', '%20').replace('\n', '%0D%0A')
            gmail_link = f"https://mail.google.com/mail/?view=cm&fs=1&to={email}&su={assunto}&body={mensagem_encoded}"
            st.write(f"📧 **{email}** — Plano: {plano}")
            st.markdown(f'<a href="{gmail_link}" target="_blank" rel="noopener noreferrer">✅ Abrir no Gmail</a>', unsafe_allow_html=True)

    if proximos_1dia:
        st.markdown("### 🔴 Expiram em 1 dia")
        for email, info in proximos_1dia:
            plano = info.get("plano", "n/a")
            assunto = "Última chance: seu acesso expira amanhã"
            mensagem = (
                f"Olá!\n\n"
                f"Este é o último lembrete: seu acesso ao Radar B3 expira amanhã.\n"
                f"Renove agora para não perder seus alertas e análises.\n\n"
                f"Link: https://seusite.com/renovar\n\n"
                f"Abraços,\n"
                f"Time Radar B3"
            )
            mensagem_encoded = mensagem.replace(' ', '%20').replace('\n', '%0D%0A')
            gmail_link = f"https://mail.google.com/mail/?view=cm&fs=1&to={email}&su={assunto}&body={mensagem_encoded}"
            st.write(f"📧 **{email}** — Plano: {plano}")
            st.markdown(f'<a href="{gmail_link}" target="_blank" rel="noopener noreferrer">✅ Abrir no Gmail</a>', unsafe_allow_html=True)

    if expirados:
        st.markdown("### ⚠️ Já expiraram")
        for email, info in expirados:
            plano = info.get("plano", "n/a")
            assunto = "Volte para o Radar B3 com desconto especial"
            mensagem = (
                f"Olá!\n\n"
                f"Sentimos sua falta! Seu acesso expirou, mas temos uma oferta especial para você voltar.\n"
                f"10% de desconto na primeira mensalidade. Aceita?\n\n"
                f"Entre em contato: https://seusite.com/contato\n\n"
                f"Abraços,\n"
                f"Time Radar B3"
            )
            mensagem_encoded = mensagem.replace(' ', '%20').replace('\n', '%0D%0A')
            gmail_link = f"https://mail.google.com/mail/?view=cm&fs=1&to={email}&su={assunto}&body={mensagem_encoded}"
            st.write(f"📧 **{email}** — Plano: {plano}")
            st.markdown(f'<a href="{gmail_link}" target="_blank" rel="noopener noreferrer">✅ Abrir no Gmail</a>', unsafe_allow_html=True)

    if not proximos_3dias and not proximos_1dia and not expirados:
        st.info("✅ Nenhum cliente próximo da expiração ou expirado.")

# ========================
# INFORMAÇÃO FINAL
# ========================
st.markdown("---")
st.caption(f"📁 Arquivo principal: `{ARQUIVO}`")
st.caption(f"📥 Solicitações: `{PENDENTES_FILE}`")
st.caption(f"💾 Backups salvos na pasta: `{BACKUP_DIR}`")