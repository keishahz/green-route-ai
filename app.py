import streamlit as st
import pandas as pd
import networkx as nx
import folium
from streamlit_folium import st_folium

# ---------------------------------------------------------
# 1. KONFIGURASI HALAMAN & TEMA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Green-Route AI Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 2. CUSTOM CSS (TAMPILAN PRO / DARK MODE)
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Background Utama Gelap */
    .stApp {
        background-color: #0E1117;
    }

    /* Font Judul Futuristik */
    h1, h2, h3 {
        font-family: 'Segoe UI', sans-serif;
        color: #FFFFFF;
        font-weight: 600;
    }

    /* Styling Kotak Metrik (Card Effect) */
    div[data-testid="stMetric"] {
        background-color: #262730;
        border: 1px solid #41444C;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }
    div[data-testid="stMetricLabel"] {
        color: #B0B3B8;
        font-size: 14px;
    }
    div[data-testid="stMetricValue"] {
        color: #00CC66; /* Hijau Neon */
        font-size: 24px;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }

    /* Header Custom */
    .header-style {
        font-size: 20px;
        font-weight: bold;
        color: white;
        margin-bottom: 20px;
        border-bottom: 2px solid #FF0000; /* Merah Pertamina */
        padding-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. HEADER DASHBOARD
# ---------------------------------------------------------
col_h1, col_h2 = st.columns([1, 6])
with col_h1:
    # Placeholder Logo (Bisa diganti jika ada link logo sendiri)
    st.markdown("## 🚛") 
with col_h2:
    st.markdown("<h1 style='padding-top:0px;'>Green-Route AI Command Center</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#B0B3B8; margin-top:-15px;'>Integrated Terminal Semarang | Intelligent Distribution System</p>", unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------
# 4. DATA BACKEND (DUMMY NODE & EDGE)
# ---------------------------------------------------------
# Koordinat Titik Penting Semarang
nodes = {
    "Terminal BBM (Pengapon)": [-6.960, 110.440], 
    "SPBU Kaligawe": [-6.955, 110.455],           
    "SPBU Simpang Lima": [-6.990, 110.425],       
    "SPBU Banyumanik": [-7.060, 110.415],         
    "SPBU Krapyak": [-6.985, 110.380]             
}

# Definisi Jalur (Edges): (Dari, Ke, Jarak KM)
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
# 5. SIDEBAR (CONTROLLER)
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Live Monitoring Panel")
    st.info("Status Sistem: ONLINE")
    
    st.markdown("---")
    st.markdown("**1. Sensor Lingkungan (IoT)**")
    is_rob_kaligawe = st.checkbox("🌊 Deteksi Banjir Rob (Kaligawe)", value=False)
    is_macet_kota = st.checkbox("🚗 Deteksi Kemacetan (Pusat Kota)", value=False)
    
    st.markdown("---")
    st.markdown("**2. Parameter Armada**")
    avg_speed = st.slider("Kecepatan Rata-rata (km/jam)", 10, 80, 40)
    
    st.markdown("---")
    st.caption("v1.0.2 Beta Build | Pertamina Eco-Innovation")

# ---------------------------------------------------------
# 6. ENGINE ALGORITMA (PATHFINDING)
# ---------------------------------------------------------
fuel_factor = 0.5   # Liter/km
emission_factor = 2.68 # kg CO2/Liter

# Membangun Graph
G = nx.Graph()
for u, v, dist in edges:
    weight = dist
    # Logika Hukuman (Penalty)
    if is_rob_kaligawe and ("Kaligawe" in u or "Kaligawe" in v):
        weight = dist * 999 # Hampir mustahil dilewati
    if is_macet_kota and ("Simpang Lima" in u or "Simpang Lima" in v):
        weight = dist * 5   # Macet parah
    
    G.add_edge(u, v, weight=weight, distance=dist)

# ---------------------------------------------------------
# 7. VISUALISASI UTAMA
# ---------------------------------------------------------
col_main_1, col_main_2 = st.columns([2, 1])

with col_main_1:
    st.markdown('<div class="header-style">📍 Geospatial Tracking Map</div>', unsafe_allow_html=True)
    
    # Peta Mode Malam (Dark Matter)
    m = folium.Map(location=[-6.98, 110.43], zoom_start=12, tiles="CartoDB dark_matter")

    # Marker Lokasi
    for name, coords in nodes.items():
        color = "#FF0000" if "Terminal" in name else "#3388FF"
        icon = "industry" if "Terminal" in name else "gas-pump"
        folium.Marker(
            coords, popup=name, tooltip=name,
            icon=folium.Icon(color="black", icon_color=color, prefix="fa", icon=icon)
        ).add_to(m)

    # Garis Jalur Normal (Putih transparan putus-putus)
    for u, v, d in edges:
        folium.PolyLine([nodes[u], nodes[v]], color="white", weight=1, opacity=0.3, dash_array="5, 5").add_to(m)

    # Input User (Di atas peta agar jelas)
    target_spbu = st.selectbox("🎯 Pilih Tujuan Pengiriman:", list(nodes.keys())[1:])

    # Hitung Rute Terpendek
    path = []
    total_distance = 0
    try:
        path = nx.shortest_path(G, source="Terminal BBM (Pengapon)", target=target_spbu, weight="weight")
        
        # Hitung Jarak Asli
        for i in range(len(path)-1):
            u_node, v_node = path[i], path[i+1]
            total_distance += G[u_node][v_node]['distance']
            
        # Gambar Rute AI (Hijau Neon Tebal)
        path_coords = [nodes[node] for node in path]
        folium.PolyLine(
            path_coords, color="#00FF7F", weight=5, opacity=0.9, 
            tooltip="Green-Route Optimized"
        ).add_to(m)
        
    except nx.NetworkXNoPath:
        st.error("Jalur Terputus! Tidak ada akses.")

    st_folium(m, width=None, height=500)

with col_main_2:
    st.markdown('<div class="header-style">📊 Performance Analytics</div>', unsafe_allow_html=True)

    # Status Alert yang Canggih
    if is_rob_kaligawe:
        st.error("⚠️ CRITICAL ALERT: Banjir Rob di Kaligawe. Rerouting aktif.")
    elif is_macet_kota:
        st.warning("⚠️ TRAFFIC ALERT: Kemacetan Pusat Kota. Mencari alternatif.")
    else:
        st.success("✅ SYSTEM NORMAL: Jalur Optimal.")

    # Hitungan Metrik
    total_emission = total_distance * fuel_factor * emission_factor
    est_time = (total_distance / avg_speed) * 60

    # Tampilan Metrik
    st.metric("Jarak Tempuh", f"{total_distance} km")
    st.metric("Estimasi Waktu", f"{est_time:.0f} min")
    st.metric("Reduksi Emisi CO2", f"{total_emission:.2f} kg", delta="Optimal", delta_color="normal")

    st.markdown("---")
    st.markdown("#### 🛣️ Rute Navigasi")
    
    # Tampilan Turn-by-Turn
    for i, p in enumerate(path):
        if i == 0:
            st.markdown(f"🟢 **START**: {p}")
        elif i == len(path)-1:
            st.markdown(f"🏁 **FINISH**: {p}")
        else:
            st.markdown(f"⬇️ Lewat: *{p}*")
