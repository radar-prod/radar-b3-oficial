import streamlit as st

st.title("🧪 Teste de Upload")

uploaded_files = st.file_uploader(
    "📂 Envie um ou mais arquivos",
    type=None,  # ✅ aceita qualquer tipo
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} arquivo(s) recebido(s).")
    for file in uploaded_files:
        st.write(f"📄 {file.name} - {len(file.getvalue())} bytes")
else:
    st.info("ℹ️ Nenhum arquivo recebido ainda.")
