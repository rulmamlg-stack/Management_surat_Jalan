import streamlit as st
import pandas as pd
import os

# --- Konfigurasi Awal (Harus sama dengan file input) ---
DB_PATH = "dbase.xlsx"

st.set_page_config(page_title="Rekap Data Surat Jalan", layout="wide")
st.title("📊 Rekap Data Surat Jalan")
st.markdown("Filter, cari, dan unduh data Delivery Order (DO) di sini.")

# --- Fungsi Helper ---
@st.cache_data
def load_data():
    """Memuat data dari Excel dengan caching."""
    if os.path.exists(DB_PATH):
        try:
            df = pd.read_excel(DB_PATH)
            # Pastikan kolom 'Date' dan 'Tgl PO' adalah tipe datetime
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df['Tgl PO'] = pd.to_datetime(df['Tgl PO'], errors='coerce')
            return df
        except Exception as e:
            st.error(f"Gagal membaca file Excel. Pastikan formatnya benar. Error: {e}")
            return pd.DataFrame()
    else:
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("Belum ada data surat jalan tersimpan di dbase.xlsx.")
else:
    # --- 1. Sidebar untuk Filter ---
    st.sidebar.header("Opsi Filter Data")
    
    # Filter Bulan
    if 'Month' in df.columns:
        months = df['Month'].unique()
        selected_month = st.sidebar.multiselect("Pilih Bulan", sorted(months), default=months)
        df_filtered = df[df['Month'].isin(selected_month)]
    else:
        df_filtered = df

    # Filter Klien
    if 'Client' in df_filtered.columns:
        clients = df_filtered['Client'].dropna().unique()
        selected_client = st.sidebar.selectbox("Filter Berdasarkan Client", 
                                               ['Semua'] + sorted(clients))
        if selected_client != 'Semua':
            df_filtered = df_filtered[df_filtered['Client'] == selected_client]

    # Filter Range Tanggal
    # Filter Range Tanggal
    if not df.empty and 'Date' in df.columns and df['Date'].notna().any():
        # Pastikan kolom Date di seluruh data (df) adalah datetime
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Ambil min/max date dari SELURUH data (df) untuk batas input
        full_min_date = df['Date'].min().date()
        full_max_date = df['Date'].max().date()
        
        # Terapkan tanggal awal dan akhir dari data yang sudah difilter untuk default value
        # Jika df_filtered kosong, gunakan batas dari full data
        default_start_date = df_filtered['Date'].min().date() if not df_filtered.empty else full_min_date
        default_end_date = df_filtered['Date'].max().date() if not df_filtered.empty else full_max_date
        
        # Jika tanggal min/max filtered tidak valid (misal, karena filter bulan kosong), gunakan full data
        try:
             date_range = st.sidebar.date_input("Pilih Rentang Tanggal", 
                                                [default_start_date, default_end_date],
                                                min_value=full_min_date,
                                                max_value=full_max_date)
        except ValueError:
             # Fallback jika default date bermasalah
             date_range = st.sidebar.date_input("Pilih Rentang Tanggal", 
                                                [full_min_date, full_max_date],
                                                min_value=full_min_date,
                                                max_value=full_max_date)
        
        
        if len(date_range) == 2:
            start_date = pd.to_datetime(date_range[0]).normalize()
            end_date = pd.to_datetime(date_range[1]).normalize()
            
            # Terapkan filter tanggal ke data yang sudah difilter (df_filtered)
            df_filtered = df_filtered[
                (df_filtered['Date'].dt.normalize() >= start_date) & 
                (df_filtered['Date'].dt.normalize() <= end_date)
            ]

    st.subheader(f"Data Tampil ({len(df_filtered)} dari {len(df)} total baris)")

    # --- KOREKSI KRUSIAL: Konversi Tipe Data sebelum data_editor ---
    # Konversi kolom 'Keterangan' (yang mungkin dibaca float karena NaN) ke string
    if 'Keterangan' in df_filtered.columns:
        df_filtered['Keterangan'] = df_filtered['Keterangan'].astype(str)
        
    # --- 2. Tampilkan DataFrame Interaktif ---
    # Menggunakan st.data_editor agar bisa disorting dan dicari
    st.data_editor(
        df_filtered.reset_index(drop=True),
        use_container_width=True,
        # Mengatur beberapa kolom agar tampilan lebih rapi
        column_config={
            "Date": st.column_config.DatetimeColumn("Date", format="YYYY/MM/DD"),
            "Tgl PO": st.column_config.DatetimeColumn("Tgl PO", format="YYYY/MM/DD"),
            "Qty": st.column_config.NumberColumn("Qty", format="%.0f Liter"),
            "Keterangan": st.column_config.TextColumn("Keterangan", width="small")
        },
        height=500
    )
    
    # --- 3. Hitung Rekap Total ---
    
    col_total_qty, col_total_do = st.columns(2) # Membuat dua kolom untuk metrik

    # Menghitung Total Quantity
    if 'Qty' in df_filtered.columns:
        # Menghitung total Quantity (volume) dari data yang difilter
        total_qty = df_filtered['Qty'].sum()
        with col_total_qty:
            st.metric(
                label="TOTAL QTY TAMPIL (Liter)", 
                value=f"{total_qty:,.0f}"
            )
    
    # Menghitung Total Jumlah Surat Jalan (Jumlah Baris)
    with col_total_do:
        st.metric(
            label="TOTAL SURAT JALAN TAMPIL", 
            value=f"{len(df_filtered)}"
        )
    
    st.divider()

    # --- 4. Tombol Download ---
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download Data Tampil ke CSV",
        data=csv,
        file_name='rekap_surat_jalan_filtered.csv',
        mime='text/csv',
    )