import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import json

st.set_page_config(page_title="Arq. Supervisor 2025", layout="wide")

# Crear carpetas
for folder in ["obras", "obras/fotos"]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Presupuesto fijo
PRESUPUESTOS = {
    #monto aplica para los dos
    "rinconada": 99524,
    "pachacutec": 99524
}

OBRAS = {
    "rinconada": "La Rinconada – La Molina",
    "pachacutec": "Ciudad Pachacútec – Ventanilla"
}

CATEGORIAS_GASTOS = ["Materiales", "Mano de obra", "Equipos", "Transporte", "Otros"]

# ====== AUTENTICACIÓN (igual que antes, corregida) ======
def check_password():
    def password_entered():
        users = st.secrets["users"]
        if (st.session_state["password"] == users["jefe_pass"] and st.session_state["user"] == users["jefe_user"]):
            st.session_state["auth"] = "jefe"
            st.session_state["username"] = st.session_state["user"]
        elif (st.session_state["password"] == users["pasante_pass"] and st.session_state["user"].startswith(users["pasante_user_prefix"])):
            st.session_state["auth"] = st.session_state["user"]
            st.session_state["username"] = st.session_state["user"]
        else:
            st.session_state["auth"] = False

    if "auth" not in st.session_state:
        st.title("ARQ. SUPERVISOR 2025")
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

# ====== OBRA ======
if st.session_state["auth"] == "jefe":
    obra_actual = st.sidebar.selectbox("Seleccionar obra", options=list(OBRAS.keys()), format_func=lambda x: OBRAS[x])
else:
    try:
        obra_actual = st.session_state["auth"].split("-")[1]
        if obra_actual not in OBRAS:
            st.error("Obra no reconocida.")
            st.stop()
    except:
        st.error("Usuario inválido.")
        st.stop()

st.sidebar.success(f"**Obra:** {OBRAS[obra_actual]}")
if st.session_state["auth"] == "jefe":
    st.sidebar.success("**MODO JEFE** – Acceso total")
else:
    st.sidebar.info("**MODO PASANTE** – Registro diario")

# ====== DATOS ======
def cargar(obra):
    archivo = f"obras/{obra}.json"
    plantilla = {"gastos": [], "avance": []}
    if os.path.exists(archivo):
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return plantilla
    else:
        guardar(obra, plantilla)
        return plantilla

def guardar(obra, datos):
    with open(f"obras/{obra}.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, default=str)

datos = cargar(obra_actual)

# ====== CÁLCULOS ======
df_gastos = pd.DataFrame(datos.get("gastos", []))
if not df_gastos.empty:
    df_gastos['fecha'] = pd.to_datetime(df_gastos['fecha'])
    hoy = date.today()
    gasto_hoy = df_gastos[df_gastos['fecha'] == pd.Timestamp(hoy)]['monto_total'].sum()
    gasto_acumulado = df_gastos['monto_total'].sum()
else:
    gasto_hoy = gasto_acumulado = 0.0

presupuesto = PRESUPUESTOS[obra_actual]
porcentaje = (gasto_acumulado / presupuesto * 100) if presupuesto > 0 else 0

# ====== SEMÁFORO DESTACADO ======
st.title(f" Obra: {OBRAS[obra_actual]}")

# Fondo con contrato (opcional - si quieres quitarlo, comenta la línea)
# st.image("https://i.imgur.com/EXAMPLE.jpg", use_column_width=True, caption="Contrato de Obra - Suma Alzada")  # Sube tu imagen a imgur y pon el link

st.markdown("---")
st.markdown("<h1 style='text-align: center;'> SEMÁFORO DE PRESUPUESTO (CONTROL DE RENTABILIDAD)</h1>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("**Presupuesto Total**", f"S/ {presupuesto:,.0f}")
with col2:
    st.metric("**Gasto Diario (Hoy)**", f"S/ {gasto_hoy:,.2f}")
with col3:
    st.metric("**Gasto Acumulado**", f"S/ {gasto_acumulado:,.2f}")
with col4:
    st.metric("**% Consumido**", f"{porcentaje:.2f}%")

# Semáforo grande con color real
if porcentaje <= 95:
    color = "#00FF00"  # Verde
    estado = "Bueno"
    mensaje = "Ejecución dentro del rango esperado. ¡Todo en orden!"
elif porcentaje <= 100:
    color = "#FFFF00"  # Ámbar
    estado = "Cuidado"
    mensaje = "Alerta preventiva: se recomienda tomar acciones de control."
else:
    color = "#FF0000"  # Rojo
    estado = "Peligro"
    mensaje = "¡Sobrepaso del presupuesto! Riesgo de pérdida. Acciones correctivas urgentes."

st.markdown(f"""
<div style='text-align: center; padding: 20px; background-color: {color}; border-radius: 15px; margin: 20px 0;'>
    <h1>{estado}</h1>
    <h3>{mensaje}</h3>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ====== PARTE DIARIO ======
st.header("📋 Parte Diario del Día")
st.info(f"**Fecha actual:** {date.today().strftime('%d/%m/%Y')}")

nombre_guardado = st.session_state.get("username", "")
responsable = st.text_input("Tu nombre", value=nombre_guardado, disabled=False)

st.subheader(" Gastos del día")
gastos_dia = {}
total_dia = 0.0
for cat in CATEGORIAS_GASTOS:
    c1, c2 = st.columns([3,1])
    with c1:
        detalle = st.text_input(f"Detalle ({cat})", key=f"det_{cat}")
    with c2:
        monto = st.number_input("Monto (S/)", min_value=0.0, step=100.0, key=f"mon_{cat}")
    if monto > 0:
        gastos_dia[cat] = {"detalle": detalle, "monto": monto}
        total_dia += monto

st.success(f"**Monto total diario:** S/ {total_dia:,.2f}")

avance = st.slider("Avance logrado hoy (%)", 0, 30, 5)
obs = st.text_area("Observaciones")
fotos = st.file_uploader("📸 Fotos del avance (mínimo 3 para pasantes)", accept_multiple_files=True, type=["jpg","png","jpeg"])

if st.button(" ENVIAR PARTE DIARIO", type="primary", use_container_width=True):
    if "pasante" in st.session_state["auth"] and len(fotos) < 3:
        st.error("¡Pasante: debes subir mínimo 3 fotos!")
    else:
        rutas = []
        for f in fotos:
            ts = datetime.now().strftime("%Y%m%d%H%M%S")
            ruta = f"obras/fotos/{obra_actual}_{date.today()}_{ts}_{f.name}"
            with open(ruta, "wb") as file:
                file.write(f.getbuffer())
            rutas.append(ruta)

        datos["avance"].append({
            "fecha": str(date.today()),
            "responsable": responsable,
            "avance": avance,
            "obs": obs,
            "fotos": rutas,
            "monto_total_dia": total_dia
        })

        if gastos_dia:
            datos["gastos"].append({
                "fecha": str(date.today()),
                "gastos": gastos_dia,
                "monto_total": total_dia
            })

        guardar(obra_actual, datos)
        st.success("¡Parte diario enviado con éxito!")
        st.balloons()
        st.rerun()

# ====== HISTORIAL ======
st.header(" 📜 Historial de Avances")
df_avance = pd.DataFrame(datos.get("avance", []))
if not df_avance.empty:
    df_avance['fecha'] = pd.to_datetime(df_avance['fecha'])
    df_avance = df_avance.sort_values(by='fecha', ascending=False)
    acum = 0
    for _, row in df_avance.iterrows():
        acum += row['avance']
        with st.expander(f"📅 {row['fecha'].strftime('%d/%m/%Y')} - {row['responsable']} | +{row['avance']}% | Acum: {acum:.1f}% | Gasto: S/ {row['monto_total_dia']:,.2f}"):
            st.write(f"**Observaciones:** {row['obs']}")
            if row['fotos']:
                st.write("**Fotos:**")
                cols = st.columns(3)
                for i, foto in enumerate(row['fotos'][:3]):
                    if os.path.exists(foto):
                        with cols[i]:
                            st.image(foto, use_column_width=True)
else:
    st.info("Aún no hay registros para esta obra.")



