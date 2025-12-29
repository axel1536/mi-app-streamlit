# PEGA ESTE CÓDIGO COMPLETO (es el definitivo con acceso restringido)
import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import json
# import base64 # <-- MEJORA: Eliminado porque no se usaba

st.set_page_config(page_title="Arq. Supervisor 2025", layout="wide")

# Crear carpetas si no existen
for folder in ["obras", "obras/fotos", "obras/evidencia"]:
    if not os.path.exists(folder):
        os.makedirs(folder)

OBRAS = {
    "rinconada": "La Rinconada – La Molina",
    "pachacutec": "Ciudad Pachacútec – Ventanilla"
}

# ====== AUTENTICACIÓN SEGURA CON SECRETS ======
def check_password():
    def password_entered():
        # <-- MEJORA: Usar st.secrets para mayor seguridad
        users = st.secrets["users"]
        if (st.session_state["password"] == users["jefe_pass"] and
            st.session_state["user"] == users["jefe_user"]):
            st.session_state["auth"] = "jefe"
        elif (st.session_state["password"] == users["pasante_pass"] and
              st.session_state["user"].startswith(users["pasante_user_prefix"])):
            st.session_state["auth"] = st.session_state["user"]
        else:
            st.session_state["auth"] = False

    if "auth" not in st.session_state:
        st.title("CONTROL DE OBRAS 2025")
        st.text_input("Usuario", key="user")
        st.text_input("Contraseña", type="password", key="password")
        st.button("INGRESAR", on_click=password_entered)
        return False
    if not st.session_state["auth"]:
        st.error("Usuario o contraseña incorrecta")
        return False
    return True

if not check_password():
    st.stop()

# ====== DETERMINAR OBRA ======
if st.session_state["auth"] == "jefe":
    obra_actual = st.sidebar.selectbox("Seleccionar obra", options=list(OBRAS.keys()), format_func=lambda x: OBRAS[x])
else:
    obra_actual = st.session_state["auth"].split("-")[1]
    st.sidebar.success(f"Obra asignada: {OBRAS[obra_actual]}")

# ====== CARGA Y GUARDA ======
def cargar(obra):
    archivo = f"obras/{obra}.json"
    if os.path.exists(archivo):
        # <-- MEJORA: Añadido try-except para mayor robustez
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.error(f"Error al leer el archivo de la obra {obra}. El archivo podría estar corrupto.")
            return {"info": OBRAS[obra], "avance": [], "cambios": [], "stock": [], "caja": []}
    else:
        plantilla = {"info": OBRAS[obra], "avance": [], "cambios": [], "stock": [], "caja": []}
        guardar(obra, plantilla)
        return plantilla

def guardar(obra, datos):
    with open(f"obras/{obra}.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, default=str)

datos = cargar(obra_actual)
df_avance = pd.DataFrame(datos.get("avance", []))

# ====== INTERFAZ PRINCIPAL ======
st.title(f"Obra: {OBRAS[obra_actual]}")
if st.session_state["auth"] == "jefe":
    st.sidebar.success("MODO JEFE – Acceso total")
else:
    st.sidebar.info("MODO PASANTE – Solo parte diario de hoy")

# Parte diario
st.header("Parte Diario del Día")
hoy = date.today()
responsable = st.text_input("Tu nombre", value=st.session_state.get("user", ""))
avance = st.slider("Avance logrado hoy (%)", 0, 30, 5)
obs = st.text_area("Observaciones")
fotos = st.file_uploader("Fotos del avance (mínimo 3)", accept_multiple_files=True, type=["jpg","png","jpeg"])

if st.button("ENVIAR PARTE DIARIO", type="primary"):
    if "pasante" in st.session_state["auth"] and len(fotos) < 3:
        st.error("¡Sube mínimo 3 fotos!")
    else:
        rutas_fotos = []
        for f in fotos:
            # Usar un timestamp para evitar nombres de archivo duplicados
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            ruta = f"obras/fotos/{obra_actual}{hoy}{timestamp}_{f.name}"
            with open(ruta, "wb") as file:
                file.write(f.getbuffer())
            rutas_fotos.append(ruta)
        
        nuevo_avance = {
            "fecha": str(hoy), 
            "responsable": responsable, 
            "avance": avance, 
            "obs": obs, 
            "fotos": rutas_fotos # <-- MEJORA: Guardar las rutas completas
        }
        datos["avance"].append(nuevo_avance)
        guardar(obra_actual, datos)
        st.success("¡Parte enviado correctamente!")
        st.balloons()
        st.rerun() # <-- MEJORA: Recargar la página para limpiar el formulario

# Mostrar historial de avances
st.header("Historial de Avances")
# <-- MEJORA: Comprobación más explícita de DataFrame vacío
if not df_avance.empty:
    # Convertir la columna de fecha a datetime para ordenar
    df_avance['fecha'] = pd.to_datetime(df_avance['fecha'])
    df_avance = df_avance.sort_values(by='fecha', ascending=False)

    for index, row in df_avance.iterrows():
        with st.expander(f"Avance del {row['fecha'].strftime('%d/%m/%Y')} - Responsable: {row['responsable']} ({row['avance']}%)"):
            st.write(f"*Observaciones:* {row['obs']}")
            # <-- MEJORA: Mostrar las fotos si existen
            if 'fotos' in row and row['fotos']:
                st.write("*Fotos del avance:*")
                # Mostrar hasta 3 fotos en una columna
                cols = st.columns(min(len(row['fotos']), 3))
                for i, foto_path in enumerate(row['fotos']):
                    if os.path.exists(foto_path):
                        with cols[i % 3]:
                            st.image(foto_path, caption=foto_path.split('/')[-1], use_column_width=True)
                    else:
                        with cols[i % 3]:
                            st.warning(f"No se encontró la imagen: {foto_path}")
else:
    st.info("No hay partes diarios registrados para esta obra aún.")