import streamlit as st
import sqlite3
from datetime import datetime
import urllib.parse

# Ruta segura en tu carpeta de usuario
DB_RUTA = r"C:\Users\ANGEL\mototaxi_pueblo.db"

# Inicializar Base de Datos
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
            fecha TEXT,
            FOREIGN KEY (conductor_id) REFERENCES conductores (id)
        )
    """)
    conexion.commit()
    conexion.close()

inicializar_bd()

# Configuración de la página web
st.set_page_config(page_title="Mototaxi El Pueblo", page_icon="🛵", layout="centered")

st.title("🛵 Sistema de Mototaxi & Delivery")
st.subheader("¡El transporte oficial de nuestro pueblo!")

# Menú lateral
menu = st.sidebar.selectbox("Menú de Opciones", ["Registrar Viaje / Pedido", "Ver Historial y Ganancias", "Gestionar Conductores"])

# --- OPCIÓN 1: REGISTRAR VIAJE ---
if menu == "Registrar Viaje / Pedido":
    st.header("📝 Nuevo Servicio")
    
    conexion = sqlite3.connect(DB_RUTA)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, placa FROM conductores")
    conductores = cursor.fetchall()
    conexion.close()
    
    if not conductores:
        st.warning("⚠️ No hay conductores registrados todavía. Ve al menú 'Gestionar Conductores' para agregar al menos uno.")
    else:
        with st.form("form_viaje"):
            cliente = st.text_input("Nombre del Cliente")
            tel_cliente = st.text_input("Teléfono del Cliente")
            origen = st.text_input("Punto de Partida (Ej. Parque Central, Tienda de Don Pepe)")
            destino = st.text_input("Punto de Destino (Ej. Barrio San Juan, Calle 4)")
            tipo_servicio = st.selectbox("Tipo de Servicio", ["Transporte de Personas", "Delivery / Mandados"])
            tarifa = st.number_input("Tarifa Total ($)", min_value=0.0, step=0.50)
            
            conductor_dict = {f"{c[1]} (Placa: {c[2]})": c[0] for c in conductores}
            conductor_seleccionado = st.selectbox("Asignar Conductor", list(conductor_dict.keys()))
            
            submit = st.form_submit_button("🚀 Registrar y Generar Ruta")
            
            if submit:
                if cliente and origen and destino and tarifa > 0:
                    c_id = conductor_dict[conductor_seleccionado]
                    comision = tarifa * 0.15 
                    pago_cond = tarifa - comision
                    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    conexion = sqlite3.connect(DB_RUTA)
                    cursor = conexion.cursor()
                    cursor.execute("""
                        INSERT INTO viajes (cliente, telefono_cliente, origen, destino, tipo_servicio, tarifa, comision_app, ganancia_conductor, conductor_id, fecha)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (cliente, tel_cliente, origen, destino, tipo_servicio, tarifa, comision, pago_cond, c_id, fecha))
                    conexion.commit()
                    conexion.close()
                    
                    st.success("¡Viaje registrado con éxito!")
                    
                    st.markdown("---")
                    st.markdown(f"### 💰 Resumen Financiero")
                    st.info(f"**Tarifa Total:** ${tarifa:.2f}\n\n🏢 **Tu Comisión (15%):** ${comision:.2f}\n\n🛵 **Para el Conductor:** ${pago_cond:.2f}")
                    
                    link_maps = f"https://www.google.com/maps/dir/?api=1&destination={urllib.parse.quote(destino)}&origin={urllib.parse.quote(origen)}"
                    
                    st.markdown(f"### 🗺️ Navegación Exacta")
                    st.markdown(f"Mándale este enlace al conductor para que le abra el mapa directo en su celular:")
                    st.markdown(f"[🔗 Abrir Ruta en Google Maps]({link_maps})")
                else:
                    st.error("Por favor completa todos los campos obligatorios y asegúrate de que la tarifa sea mayor a 0.")

# --- OPCIÓN 2: HISTORIAL Y GANANCIAS ---
elif menu == "Ver Historial y Ganancias":
    st.header("📊 Historial de Viajes y Caja")
    
    conexion = sqlite3.connect(DB_RUTA)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT v.id, v.cliente, v.origen, v.destino, v.tarifa, v.comision_app, c.nombre, v.fecha 
        FROM viajes v LEFT JOIN conductores c ON v.conductor_id = c.id
        ORDER BY v.id DESC
    """)
    viajes = cursor.fetchall()
    
    cursor.execute("SELECT SUM(tarifa), SUM(comision_app) FROM viajes")
    totales = cursor.fetchone()
    conexion.close()
    
    total_recaudado = totales[0] if totales[0] else 0.0
    total_comision = totales[1] if totales[1] else 0.0
    
    col1, col2 = st.columns(2)
    col1.metric("Dinero Movido en el Pueblo", f"${total_recaudado:.2f}")
    col2.metric("Tus Ganancias Totales (15%)", f"${total_comision:.2f}")
    
    st.markdown("---")
    st.subheader("📋 Lista de Servicios Realizados")
    
    if not viajes:
        st.info("Aún no hay viajes registrados.")
    else:
        for v in viajes:
            st.markdown(f"""
            * **ID #{v[0]}** | Cliente: **{v[1]}**
              * 📍 Ruta: `{v[2]}` ➡️ `{v[3]}`
              * 💵 Tarifa: **${v[4]:.2f}** (Tu comisión: ${v[5]:.2f})
              * 🛵 Conductor: {v[6]} | ⏰ {v[7]}
            """)
            st.markdown("---")

# --- OPCIÓN 3: GESTIONAR CONDUCTORES ---
elif menu == "Gestionar Conductores":
    st.header("👥 Gestión de Conductores")
    
    with st.form("form_conductor"):
        nombre = st.text_input("Nombre del Conductor")
        telefono = st.text_input("Teléfono / WhatsApp")
        placa = st.text_input("Placa de la Moto")
        submitted = st.form_submit_button("Registrar Conductor")
        
        if submitted:
            if nombre and telefono and placa:
                conexion = sqlite3.connect(DB_RUTA)
                cursor = conexion.cursor()
                cursor.execute("INSERT INTO conductores (nombre, telefono, placa) VALUES (?, ?, ?)", (nombre, telefono, placa))
                conexion.commit()
                conexion.close()
                st.success(f"¡Conductor {nombre} agregado con éxito!")
            else:
                st.error("Completa todos los campos del conductor.")
                
    st.markdown("---")
    st.subheader("Conductores Actuales en la Red")
    conexion = sqlite3.connect(DB_RUTA)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, telefono, placa FROM conductores")
    conds = cursor.fetchall()
    conexion.close()
    
    if not conds:
        st.info("No hay conductores registrados.")
    else:
        for c in conds:
            st.text(f"ID: {c[0]} | Nombre: {c[1]} | Tel: {c[2]} | Placa: {c[3]}")