# ========================
# CSS: VITRINE PRIMEIRO, SIDEBAR DEPOIS (NO CELULAR)
# ========================
mobile_order_css = """
<style>
@media (max-width: 768px) {
    /* Força o container principal a usar coluna */
    .stApp {
        display: flex !important;
        flex-direction: column !important;
    }
    /* Conteúdo principal (vitrine ou sistema) */
    .stMain {
        order: 1 !important;
        margin-left: 0 !important;
        padding: 10px !important;
    }
    /* Barra lateral */
    .stSidebar {
        order: 2 !important;
        position: static !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: auto !important;
        background-color: #f8f9fa !important;
        padding: 15px !important;
        border-right: none !important;
        border-bottom: 1px solid #e0e0e0 !important;
        z-index: auto !important;
        box-shadow: none !important;
    }
    /* Remove o cabeçalho da sidebar (seta) */
    .stSidebar [data-testid="stSidebarHeader"] {
        display: none !important;
    }
    /* Ajusta o conteúdo da sidebar */
    .stSidebar > div:first-child {
        padding-top: 20px !important;
    }
    /* Garante que a vitrine não seja cortada */
    .stMain > div:first-child {
        z-index: auto !important;
    }
}
</style>
"""
st.markdown(mobile_order_css, unsafe_allow_html=True)
