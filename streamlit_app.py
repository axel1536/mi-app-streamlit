# PEGA ESTE CÓDIGO COMPLETO (es el definitivo con acceso restringido)
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

# Presupuesto fijo por obra (según instructivo y contrato)
PRESUPUESTOS = {
    "rinconada": 0,  # Si hay otra obra, poner su monto aquí
    "pachacutec": 99524  # S/ 99,524 del contrato del muro de contención
}

OBRAS = {
    "rinconada": "La Rinconada – La Molina",
    "pachacutec": "Ciudad Pachacútec – Ventanilla"
}

CATEGORIAS_GASTOS = ["Materiales", "Mano de obra", "Equipos", "Transporte", "Otros"]

# ====== AUTENTICACIÓN ======
def check_password():
    def password_entered():
        users = st.secrets["users"]
        if (st.session_state["password"] == users["jefe_pass"] and st.session_state["user"] == users["jefe_user"]):
            st.session_state["auth"] = "jefe"
        elif (st.session_state["password"] == users["pasante_pass"] and st.session_state["user"].startswith(users["pasante_user_prefix"])):
            st.session_state["auth"] = st.session_state["user"]
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

# ====== DETERMINAR OBRA ======
if st.session_state["auth"] == "jefe":
    obra_actual = st.sidebar.selectbox("Seleccionar obra", options=list(OBRAS.keys()), format_func=lambda x: OBRAS[x])
else:
    try:
        obra_actual = st.session_state["auth"].split("-")[1]
        if obra_actual not in OBRAS:
            st.error("Obra no reconocida en tu usuario.")
            st.stop()
    except:
        st.error("Usuario pasante con formato inválido.")
        st.stop()

st.sidebar.success(f"Obra: {OBRAS[obra_actual]}")
if st.session_state["auth"] == "jefe":
    st.sidebar.success("MODO JEFE – Acceso total")
else:
    st.sidebar.info("MODO PASANTE – Registro diario")

# ====== CARGA Y GUARDA ======
def cargar(obra):
    archivo = f"obras/{obra}.json"
    plantilla = {
        "info": OBRAS[obra],
        "gastos": [],      # Lista de registros diarios de gastos
        "avance": []       # Lista de partes diarios
    }
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

# ====== CÁLCULOS DE GASTOS ======
df_gastos = pd.DataFrame(datos.get("gastos", []))
if not df_gastos.empty:
    df_gastos['fecha'] = pd.to_datetime(df_gastos['fecha'])
    hoy = date.today()
    gasto_hoy = df_gastos[df_gastos['fecha'] == pd.Timestamp(hoy)]['monto_total'].sum()
    gasto_acumulado = df_gastos['monto_total'].sum()
else:
    gasto_hoy = 0
    gasto_acumulado = 0

presupuesto = PRESUPUESTOS[obra_actual]
porcentaje_consumido = (gasto_acumulado / presupuesto * 100) if presupuesto > 0 else 0

# ====== SEMÁFORO DE PRESUPUESTO ======
st.header("🚦 Semáforo de presupuesto (control de rentabilidad)")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Presupuesto total", f"S/ {presupuesto:,.0f}")
col2.metric("Gasto diario (hoy)", f"S/ {gasto_hoy:,.2f}")
col3.metric("Gasto acumulado", f"S/ {gasto_acumulado:,.2f}")
col4.metric("% consumido", f"{porcentaje_consumido:.2f}%")

# Color del semáforo
if porcentaje_consumido <= 95:
    color = "🟢 Verde"
    alerta = "Ejecución dentro del rango esperado"
elif porcentaje_consumido <= 100:
    color = "🟡 Ámbar"
    alerta = "Alerta preventiva: tomar acciones de control"
else:
    color = "🔴 Rojo"
    alerta = "Sobrepaso del presupuesto: riesgo de pérdida"

st.markdown(f"### Estado: **{color}**")
st.info(alerta)

# ====== PARTE DIARIO DEL DÍA ======
st.header("Parte Diario del Día")
hoy = date.today()
st.write(f"**Fecha actual:** {hoy.strftime('%d/%m/%Y')}")

responsable = st.text_input("Tu nombre", value=st.session_state["user"])

st.subheader("Gastos del día")
gastos_dia = {}
monto_total_dia = 0

for categoria in CATEGORIAS_GASTOS:
    col1, col2 = st.columns([2, 1])
    with col1:
        detalle = st.text_input(f"Detalle ({categoria})", key=f"det_{categoria}")
    with col2:
        monto = st.number_input(f"Monto (S/) - {categoria}", min_value=0.0, step=100.0, key=f"monto_{categoria}")
    if monto > 0:
        gastos_dia[categoria] = {"detalle": detalle, "monto": monto}
        monto_total_dia += monto

st.write(f"**Monto total diario:** S/ {monto_total_dia:,.2f}")

avance = st.slider("Avance logrado hoy (%)", 0, 30, 5)
obs = st.text_area("Observaciones")
fotos = st.file_uploader("Fotos del avance (mínimo 3)", accept_multiple_files=True, type=["jpg","png","jpeg"])

if st.button("ENVIAR PARTE DIARIO", type="primary"):
    if "pasante" in st.session_state["auth"] and len(fotos) < 3:
        st.error("¡Debes subir mínimo 3 fotos!")
    elif monto_total_dia == 0 and avance == 0 and not obs and len(fotos) == 0:
        st.error("Debes registrar al menos un gasto, avance u observación.")
    else:
        # Guardar fotos
        rutas_fotos = []
        for f in fotos:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            ruta = f"obras/fotos/{obra_actual}_{hoy}_{timestamp}_{f.name}"
            with open(ruta, "wb") as file:
                file.write(f.getbuffer())
            rutas_fotos.append(ruta)

        # Guardar registro de avance
        datos["avance"].append({
            "fecha": str(hoy),
            "responsable": responsable,
            "avance": avance,
            "obs": obs,
            "fotos": rutas_fotos,
            "monto_total_dia": monto_total_dia
        })

        # Guardar gastos del día (solo los que tienen monto > 0)
        if gastos_dia:
            datos["gastos"].append({
                "fecha": str(hoy),
                "responsable": responsable,
                "gastos": gastos_dia,
                "monto_total": monto_total_dia
            })

        guardar(obra_actual, datos)
        st.success("¡Parte diario enviado correctamente!")
        st.balloons()
        st.rerun()

# ====== HISTORIAL DE AVANCES ======
st.header("Historial de Avances")
df_avance = pd.DataFrame(datos.get("avance", []))
if not df_avance.empty:
    df_avance['fecha'] = pd.to_datetime(df_avance['fecha'])
    df_avance = df_avance.sort_values(by='fecha', ascending=False)
    avance_acum = 0
    for _, row in df_avance.iterrows():
        avance_acum += row['avance']
        with st.expander(f"{row['fecha'].strftime('%d/%m/%Y')} - {row['responsable']} (+{row['avance']}%) → Acumulado: {avance_acum:.1f}% - Gasto día: S/ {row['monto_total_dia']:,.2f}"):
            st.write(f"**Observaciones:** {row['obs']}")
            if row['fotos']:
                st.write("**Fotos del avance:**")
                cols = st.columns(min(len(row['fotos']), 3))
                for i, foto in enumerate(row['fotos'][:3]):
                    if os.path.exists(foto):
                        with cols[i]:
                            st.image(foto, use_column_width=True)
else:
    st.info("No hay partes diarios registrados aún.")
