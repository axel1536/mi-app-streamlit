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

# === 1. CONFIGURACIÓN (solo jefe) ===
if st.session_state["auth"] == "jefe":
    with st.expander("⚙️ Configuración de Obra (Presupuesto, Cronograma, Rendimientos)", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            presupuesto = st.number_input("Presupuesto Total de Obra (S/)", min_value=0.0, value=float(datos.get("presupuesto_total", 0)))
            datos["presupuesto_total"] = presupuesto
        with col2:
            st.write("**Rendimientos de Personal (unidad/día)**")
            rendimientos = datos.get("rendimientos", {})
            labores = st.text_input("Nueva labor (ej: Carpintero)", "")
            if labores and st.button("Agregar labor"):
                if labores not in rendimientos:
                    rendimientos[labores] = 0
            for labor in list(rendimientos):
                rendimientos[labor] = st.number_input(f"{labor} (unidad/día)", min_value=0.0, value=float(rendimientos[labor]), key=f"rend_{labor}")
            datos["rendimientos"] = rendimientos

        st.write("**Cronograma Valorizado (Avance planificado % por fecha)**")
        nueva_fecha = st.date_input("Fecha planificada")
        nuevo_avance_plan = st.number_input("Avance planificado acumulado (%)", 0.0, 100.0, step=1.0)
        if st.button("Agregar al cronograma"):
            datos["cronograma"].append({"fecha": str(nueva_fecha), "avance_plan": nuevo_avance_plan})
            datos["cronograma"] = sorted(datos["cronograma"], key=lambda x: x["fecha"])
            st.success("Agregado al cronograma")
        
        if st.button("💾 Guardar Configuración"):
            guardar(obra_actual, datos)
            st.success("Configuración guardada")
            st.rerun()

# === 2. SEMÁFORO DE ALERTA ===
if datos["presupuesto_total"] > 0 or datos["cronograma"]:
    st.header("🚦 Semáforo de Alerta")
    col1, col2 = st.columns(2)
    
    # Avance real acumulado
    avance_real = sum(item["avance"] for item in datos["avance"]) if datos["avance"] else 0
    
    with col1:
        if datos["cronograma"]:
            hoy_str = str(date.today())
            plan_hoy = next((item["avance_plan"] for item in reversed(datos["cronograma"]) if item["fecha"] <= hoy_str), 0)
            desviacion_avance = avance_real - plan_hoy
            st.metric("Avance Real vs Planificado", f"{avance_real:.1f}%", f"{desviacion_avance:+.1f}%")
            
            if desviacion_avance >= -5:
                color = "🟢 Verde"
            elif desviacion_avance >= -10:
                color = "🟡 Ámbar"
            else:
                color = "🔴 Rojo"
            st.markdown(f"**Estado avance: {color}**")
    
    with col2:
        if datos["presupuesto_total"] > 0:
            gasto_estimado = datos["presupuesto_total"] * (avance_real / 100) if avance_real > 0 else 0
            desviacion_pres = ((gasto_estimado / datos["presupuesto_total"]) * 100) - avance_real
            st.metric("Desviación Presupuestal", f"{desviacion_pres:+.1f}%")
            
            if desviacion_pres <= 5:
                color_p = "🟢 Verde (cómodo)"
            elif desviacion_pres <= 10:
                color_p = "🟡 Ámbar (precaución)"
            else:
                color_p = "🔴 Rojo (pérdida)"
            st.markdown(f"**Estado presupuesto: {color_p}**")

# === 3. Parte Diario (igual que antes) ===
st.header("Parte Diario del Día")
hoy = date.today()
responsable = st.text_input("Tu nombre", value=st.session_state["user"])
avance = st.slider("Avance logrado hoy (%)", 0, 30, 5)
obs = st.text_area("Observaciones")
fotos = st.file_uploader("Fotos del avance (mínimo 3)", accept_multiple_files=True, type=["jpg","png","jpeg"])

if st.button("ENVIAR PARTE DIARIO", type="primary"):
    if "pasante" in st.session_state["auth"] and len(fotos) < 3:
        st.error("¡Sube mínimo 3 fotos!")
    else:
        rutas_fotos = []
        for f in fotos:
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
            "fotos": rutas_fotos
        }
        datos["avance"].append(nuevo_avance)
        guardar(obra_actual, datos)
        st.success("¡Parte enviado correctamente!")
        st.balloons()
        st.rerun()

# === 4. Historial ===
st.header("Historial de Avances")
if not df_avance.empty:
    df_avance['fecha'] = pd.to_datetime(df_avance['fecha'])
    df_avance = df_avance.sort_values(by='fecha', ascending=False)
    avance_acumulado = 0
    for index, row in df_avance.iterrows():
        avance_acumulado += row['avance']
        with st.expander(f"{row['fecha'].strftime('%d/%m/%Y')} - {row['responsable']} (+{row['avance']}%) → Acumulado: {avance_acumulado:.1f}%"):
            st.write(f"*Observaciones:* {row['obs']}")
            if 'fotos' in row and row['fotos']:
                st.write("*Fotos:*")
                cols = st.columns(min(len(row['fotos']), 3))
                for i, foto_path in enumerate(row['fotos'][:3]):
                    if os.path.exists(foto_path):
                        with cols[i]:
                            st.image(foto_path, use_column_width=True)
else:
    st.info("No hay partes diarios aún.")
