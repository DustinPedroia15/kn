import streamlit as st
import pandas as pd
import requests

# ---------- AUTHENTICATION ----------
api_key = st.secrets["HOLDED_API_KEY"]
PASSCODE = st.secrets["STREAMLIT_PASSCODE"]

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    user_input = st.text_input("🔐 Ingrese la contraseña", type="password")
    if user_input == PASSCODE:
        st.session_state.authenticated = True
        st.rerun()
    elif user_input:
        st.error("Contraseña incorrecta.")
    st.stop()

# ---------- FETCH WAYBILL (ALBARÁN) DATA FROM HOLDED ----------
@st.cache_data(ttl=3600)
def fetch_waybills():
    url = "https://api.holded.com/api/invoicing/v1/documents/waybill"
    headers = {
        "accept": "application/json",
        "key": api_key
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return pd.DataFrame(response.json())

# ---------- STREAMLIT UI ----------
st.set_page_config(page_title="Informe de Albaranes", layout="wide")
st.title("📦 Informe de Albaranes (Waybills) desde Holded")

st.markdown("""
Ingrese uno o más **números de albarán** (por ejemplo: ABO123456, ABO654321).  
La app buscará coincidencias exactas o parciales en los documentos de tipo albarán.
""")

abo_input = st.text_input("🔍 Números de Albarán (separados por comas):", placeholder="e.g. ABO123456, ABO654321")

if st.button("Buscar") or abo_input:
    abos = [a.strip().lower() for a in abo_input.split(",") if a.strip()]

    if not abos:
        st.warning("Por favor, introduzca al menos un número de albarán válido.")
        st.stop()

    try:
        df = fetch_waybills()
        df["docNumber_lower"] = df["docNumber"].str.lower()

        matches = pd.DataFrame()
        for ab in abos:
            matches = pd.concat([matches, df[df["docNumber_lower"].str.contains(ab)]], ignore_index=True)

        if matches.empty:
            st.warning("No se encontraron albaranes que coincidan.")
        else:
            st.success(f"Se encontraron {len(matches)} albaranes.")
            st.dataframe(matches, use_container_width=True)

            # Download CSV
            csv = matches.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📥 Descargar CSV", data=csv, file_name="albaranes_holded.csv", mime="text/csv")

    except Exception as e:
        st.error(f"Ocurrió un error al consultar los albaranes: {e}")
