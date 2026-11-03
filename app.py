import streamlit as st
import sqlite3
from datetime import datetime
import urllib.parse
import os

# Ruta automática que funciona en cualquier lugar sin dar error
DB_RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mototaxi_pueblo.db")

def inicializar_bd():
    conexion = sqlite3.connect(DB_RUTA)
    cursor = conexion.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conductores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT NOT NULL,
            placa TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS viajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            telefono_cliente TEXT NOT NULL,
            origen TEXT NOT NULL,
            destino TEXT NOT NULL,
            tipo_servicio TEXT NOT NULL,
            tarifa REAL NOT NULL,
            comision_app REAL NOT NULL,
            ganancia_conductor REAL NOT NULL,
            conductor_id INTEGER,
            estado TEXT DEFAULT 'En Curso',
            fecha TEXT,
            FOREIGN KEY (conductor_id) REFERENCES conductores (id)
        )
    """)
    conexion.commit()
    conexion.close()

inicializar_bd()

st.set_page_config(page_title="Tinaco Express", page_icon="🛵", layout="centered")
st.title("🛵 Tinaco Express - Central")
st.subheader("Control de Flota y Envíos")

menu = st.sidebar.selectbox("Menú de Opciones", ["Registrar Nuevo Viaje", "Viajes Activos (En Curso)", "Historial y Caja", "Gestionar Conductores"])

if menu == "Registrar Nuevo Viaje":
    st.header("📝 Nuevo Servicio / Pedido")
    conexion = sqlite3.connect(DB_RUTA)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, placa FROM conductores")
    conductores = cursor.fetchall()
    conexion.close()
    
    if not conductores:
        st.warning("⚠️ Registra a tus 3 motorizados en 'Gestionar Conductores' primero.")
    else:
        with st.form("form_viaje"):
            cliente = st.text_input("Nombre del Cliente")
            tel_cliente = st.text_input("Teléfono del Cliente")
            origen = st.text_input("Punto de Partida (Ej. Centro, Los Mangos)")
            destino = st.text_input("Punto de Destino")
            tipo_servicio = st.selectbox("Tipo de Servicio", ["Transporte de Personas", "Delivery / Mandados"])
            tarifa = st.number_input("Tarifa Total ($)", min_value=0.0, step=0.50)
            
            conductor_dict = {f"{c[1]} (Placa: {c[2]})": c[0] for c in conductores}
            conductor_seleccionado = st.selectbox("Asignar Motorizado", list(conductor_dict.keys()))
            
            submit = st.form_submit_button("🚀 Despachar y Generar Ruta")
            
            if submit and cliente and origen and destino and tarifa > 0:
                c_id = conductor_dict[conductor_seleccionado]
                comision = tarifa * 0.15
                pago_cond = tarifa - comision
                fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                conexion = sqlite3.connect(DB_RUTA)
                cursor = conexion.cursor()
                cursor.execute("""
                    INSERT INTO viajes (cliente, telefono_cliente, origen, destino, tipo_servicio, tarifa, comision_app, ganancia_conductor, conductor_id, estado, fecha)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'En Curso', ?)
                """, (cliente, tel_cliente, origen, destino, tipo_servicio, tarifa, comision, pago_cond, c_id, fecha))
                conexion.commit()
                conexion.close()
                
                st.success("¡Viaje despachado con éxito!")
                st.info(f"**Tarifa:** ${tarifa:.2f} | 🏢 **Tu 15%:** ${comision:.2f} | 🛵 **Motorizado:** ${pago_cond:.2f}")
                
                link_maps = f"https://www.google.com/maps/dir/?api=1&destination={urllib.parse.quote(destino)}&origin={urllib.parse.quote(origen)}"
                st.markdown(f"[🔗 Enviar Ruta en Google Maps al Motorizado]({link_maps})")

elif menu == "Viajes Activos (En Curso)":
    st.header("⚡ Viajes Activos en Tinaco")
    conexion = sqlite3.connect(DB_RUTA)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT v.id, v.cliente, v.origen, v.destino, v.tarifa, c.nombre, v.fecha 
        FROM viajes v LEFT JOIN conductores c ON v.conductor_id = c.id
        WHERE v.estado = 'En Curso'
        ORDER BY v.id DESC
    """)
    viajes_activos = cursor.fetchall()
    conexion.close()
    
    if not viajes_activos:
        st.info("No hay viajes en curso en este momento.")
    else:
        for v in viajes_activos:
            st.markdown(f"### Viaje #{v[0]} - Cliente: {v[1]}\n* 📍 `{v[2]}` ➡️ `{v[3]}`\n* 💵 `${v[4]:.2f}` | 🛵 {v[5]}")
            if st.button(f"✅ Confirmar Entrega #{v[0]}", key=f"btn_{v[0]}"):
                conexion = sqlite3.connect(DB_RUTA)
                cursor = conexion.cursor()
                cursor.execute("UPDATE viajes SET estado = 'Entregado' WHERE id = ?", (v[0],))
                conexion.commit()
                conexion.close()
                st.success("¡Entrega confirmada!")
                st.rerun()

elif menu == "Historial y Caja":
    st.header("📊 Historial y Caja")
    conexion = sqlite3.connect(DB_RUTA)
    cursor = conexion.cursor()
    cursor.execute("SELECT SUM(tarifa), SUM(comision_app) FROM viajes WHERE estado = 'Entregado'")
    totales = cursor.fetchone()
    conexion.close()
    
    total_recaudado = totales[0] if totales[0] else 0.0
    total_comision = totales[1] if totales[1] else 0.0
    
    col1, col2 = st.columns(2)
    col1.metric("Total Recaudado", f"${total_recaudado:.2f}")
    col2.metric("Tus Ganancias (15%)", f"${total_comision:.2f}")

elif menu == "Gestionar Conductores":
    st.header("👥 Mis 3 Motorizados")
    with st.form("form_conductor"):
        nombre = st.text_input("Nombre")
        telefono = st.text_input("Teléfono")
        placa = st.text_input("Placa")
        if st.form_submit_button("Registrar Motorizado") and nombre and telefono and placa:
            conexion = sqlite3.connect(DB_RUTA)
            cursor = conexion.cursor()
            cursor.execute("INSERT INTO conductores (nombre, telefono, placa) VALUES (?, ?, ?)", (nombre, telefono, placa))
            conexion.commit()
            conexion.close()
            st.success(f"¡Motorizado {nombre} guardado!")