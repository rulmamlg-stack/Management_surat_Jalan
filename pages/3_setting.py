import streamlit as st
import pandas as pd
import os
import shutil
from datetime import datetime
import json

# --- 1. Konfigurasi Path ---
DB_PATH = "dbase.xlsx"
CONFIG_PATH = "config_identitas.json" # File untuk menyimpan data identitas perusahaan
ASSETS_FOLDER = "assets"
os.makedirs(ASSETS_FOLDER, exist_ok=True) # Pastikan folder assets ada

# --- 2. Fungsi Helper ---

def load_config():
    """Memuat data konfigurasi dari file JSON."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    # Default jika file belum ada
    return {
        "Nama Perusahaan": "PT. SHA SOLO",
        "Alamat 1": "Jl. Yosodipuro No. 21 Surakarta 57131",
        "Telepon": "0271-644987 (Hunting) / 081-325-999-999",
        "Email": "sha@shasolo.com / marketing@shasolo.com",
        "Website": "www.shasolo.com"
    }

def save_config(config_data):
    """Menyimpan data konfigurasi ke file JSON."""
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config_data, f, indent=4)

# --- Halaman Streamlit ---
st.set_page_config(page_title="Pengaturan Sistem", layout="centered")
st.title("⚙️ Pengaturan Sistem")

# Muat data identitas saat aplikasi dimulai
config = load_config()

# =================================================================
## A. Pengaturan Identitas Perusahaan
# =================================================================
st.header("1. Identitas Perusahaan")
st.markdown("Data ini digunakan di seluruh aplikasi, termasuk di dokumen PDF.")

with st.form("form_identitas"):
    # Gunakan current config sebagai default value
    new_nama = st.text_input("Nama Perusahaan", value=config["Nama Perusahaan"])
    new_alamat = st.text_input("Alamat Kantor", value=config["Alamat 1"])
    new_telp = st.text_input("Telepon / HP", value=config["Telepon"])
    new_email = st.text_input("Email Kontak", value=config["Email"])
    new_web = st.text_input("Website", value=config["Website"])

    submitted_identitas = st.form_submit_button("💾 Simpan Identitas Baru")

if submitted_identitas:
    # Update config data
    config["Nama Perusahaan"] = new_nama
    config["Alamat 1"] = new_alamat
    config["Telepon"] = new_telp
    config["Email"] = new_email
    config["Website"] = new_web
    
    save_config(config)
    st.success("✅ Identitas perusahaan berhasil diperbarui dan disimpan!")
    st.rerun() # Refresh halaman untuk menampilkan data baru
    
st.divider()

# =================================================================
## B. Pengaturan Aset Gambar (Header PDF)
# =================================================================
st.header("2. Pengaturan Header & Logo")
st.info(f"Gambar header Anda saat ini tersimpan di: **{ASSETS_FOLDER}/header_sha.png**")

uploaded_file = st.file_uploader(
    "Upload Gambar Header Baru (PNG atau JPG, disarankan resolusi tinggi, lebar sekitar 18cm)", 
    type=["png", "jpg", "jpeg"]
)

if uploaded_file is not None:
    # Tentukan nama file target di folder assets
    file_extension = uploaded_file.name.split('.')[-1]
    target_path = os.path.join(ASSETS_FOLDER, "header_sha.png")
    
    # Simpan file yang diunggah
    with open(target_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    st.success(f"✅ Gambar header baru berhasil disimpan di: {target_path}. Mohon refresh halaman lain (Input & Cetak DO) untuk melihat perubahan.")

# Tampilkan preview header yang sudah ada
if os.path.exists(os.path.join(ASSETS_FOLDER, "header_sha.png")):
    st.subheader("Preview Header Saat Ini")
    st.image(os.path.join(ASSETS_FOLDER, "header_sha.png"), width=400)
else:
    st.warning("Header/Logo belum ditemukan di folder assets.")

st.divider()

# =================================================================
## C. Opsi Sistem (Backup)
# =================================================================
st.header("3. Opsi Sistem")

if st.button("📦 Backup Database"):
    if os.path.exists(DB_PATH):
        # Buat folder backup jika belum ada
        BACKUP_DIR = "backup_data"
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # Tentukan nama file backup
        today = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"dbase_backup_{today}.xlsx")
        
        # Lakukan proses copy
        shutil.copy(DB_PATH, backup_path)
        st.success(f"✅ Backup database berhasil dibuat di: **{backup_path}**")
    else:
        st.error(f"File database tidak ditemukan di: {DB_PATH}. Tidak dapat melakukan backup.")

st.info("Anda bisa mengembangkan fitur lain seperti Restore Data atau Pengaturan User di sini.")
