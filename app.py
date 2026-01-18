import streamlit as st
import pandas as pd
import networkx as nx
import folium
from streamlit_folium import st_folium

# ---------------------------------------------------------
# 1. KONFIGURASI HALAMAN
# ---------------------------------------------------------
st.set_page_config(
    page_title="Green-Route AI Prototype", 
    page_icon="🚛",
    layout="wide"
)

st.title("🚛 Green-Route AI: Smart Distribution System")
st.markdown("""
**Sistem Optimasi Distribusi BBM Dinamis Berbasis AI & Prediksi Banjir Real-Time** *Integrated Terminal Semarang - Pertamina Patra Niaga*
""")

# ---------------------------------------------------------
# 2. DATA DUMMY & GRAF (BACKEND)
# ---------------------------------------------------------
# Koordinat Titik Penting Semarang (Latitude, Longitude)
nodes = {
    "Terminal BBM (Pengapon)": [-6.960, 110.440], 
    "SPBU Kaligawe": [-6.955, 110.455],           
    "SPBU Simpang Lima": [-6.990, 110.425],       
    "SPBU Banyumanik": [-7.060, 110.415],         
    "SPBU Krapyak": [-6.985, 110.380]             
}

# Definisi Jalan (Edges): (Dari, Ke, Jarak KM)
edges = [
    ("Terminal BBM (Pengapon)", "SPBU Kaligawe", 3.0),
    ("Terminal BBM (Pengapon)", "SPBU Simpang Lima", 5.5),
    ("SPBU Kaligawe", "SPBU Banyumanik", 15.0), # Via Tol
    ("SPBU Simpang Lima", "SPBU Banyumanik", 10.0),
    ("SPBU Simpang Lima", "SPBU Krapyak", 6.0),
    ("Terminal BBM (Pengapon)", "SPBU Krapyak", 8.0),
    ("SPBU Kaligawe", "SPBU Simpang Lima", 4.0) 
]

# ---------------------------------------------------------
# 3. SIDEBAR CONTROL
# ---------------------------------------------------------
st.sidebar.header("⚙️ Control Panel (Simulasi)")

st.sidebar.subheader("1. Kondisi Lingkungan (Live API)")
is_rob_kaligawe = st.sidebar.checkbox("⚠️ Banjir Rob: Area Kaligawe", value=False)
is_macet_kota = st.sidebar.checkbox("🚗 Kemacetan: Pusat Kota", value=False)

st.sidebar.subheader("2. Parameter Armada")
avg_speed = st.sidebar.slider("Kecepatan Rata-rata (km/jam)", 20, 60, 40)
fuel_factor = 0.5  # Liter/km
emission_factor = 2.68 # kg CO2/Liter

# ---------------------------------------------------------
# 4. ALGORITMA OPTIMASI (CORE ENGINE)
# ---------------------------------------------------------
G = nx.Graph()

for u, v, dist in edges:
    weight = dist # Default cost
    
    # Logika Hukuman (Penalty) jika Banjir/Macet
    if is_rob_kaligawe and ("Kaligawe" in u or "Kaligawe" in v):
        weight = dist * 9999 # Jalan ditutup (hampir mustahil dilewati)
    
    if is_macet_kota and ("Simpang Lima" in u or "Simpang Lima" in v):
        weight = dist * 5 # Macet parah

    G.add_edge(u, v, weight=weight, distance=dist)

# User Input Tujuan
target_spbu = st.selectbox("Pilih Tujuan Pengiriman:", list(nodes.keys())[1:])

# Hitung Rute Terpendek (Dijkstra)
path = []
total_distance = 0
try:
    path = nx.shortest_path(G, source="Terminal BBM (Pengapon)", target=target_spbu, weight="weight")
    
    # Hitung Real Distance
    for i in range(len(path)-1):
        u_node, v_node = path[i], path[i+1]
        total_distance += G[u_node][v_node]['distance']

except nx.NetworkXNoPath:
    st.error("Jalur terputus total!")

# Hitung Metrik
total_emission = total_distance * fuel_factor * emission_factor
est_time = (total_distance / avg_speed) * 60

# ---------------------------------------------------------
# 5. VISUALISASI DASHBOARD
# ---------------------------------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📍 Peta Rute Cerdas")
    # Inisialisasi Peta
    m = folium.Map(location=[-6.98, 110.43], zoom_start=12)

    # Marker Titik
    for name, coords in nodes.items():
        color = "red" if "Terminal" in name else "blue"
        icon = "industry" if "Terminal" in name else "gas-pump"
        folium.Marker(
            coords, popup=name, tooltip=name,
            icon=folium.Icon(color=color, prefix="fa", icon=icon)
        ).add_to(m)

    # Garis Jalan Normal (Abu-abu)
    for u, v, d in edges:
        folium.PolyLine([nodes[u], nodes[v]], color="gray", weight=2, opacity=0.4).add_to(m)

    # Garis Rute AI (Hijau)
    if path:
        path_coords = [nodes[node] for node in path]
        folium.PolyLine(
            path_coords, color="#00CC66", weight=6, opacity=0.9, 
            tooltip="Green-Route (Optimal)"
        ).add_to(m)

    st_folium(m, width=None, height=500)

with col2:
    st.subheader("📊 Analisis Dampak")
    
    if is_rob_kaligawe:
        st.warning("⚠️ TERDETEKSI ROB!\nRute dialihkan menghindari Kaligawe.")
    elif is_macet_kota:
        st.info("ℹ️ KEMACETAN KOTA.\nMencari jalur alternatif.")
    else:
        st.success("✅ JALUR AMAN.\nMenggunakan rute standar.")

    st.metric("Jarak Tempuh", f"{total_distance} km")
    st.metric("Emisi CO2", f"{total_emission:.2f} kg", delta="- Reduksi Optimal")
    st.metric("Estimasi Waktu", f"{est_time:.0f} menit")

    st.write("---")
    st.caption("**Rute Turn-by-Turn:**")
    for i, p in enumerate(path):
        st.markdown(f"**{i+1}.** {p}")
