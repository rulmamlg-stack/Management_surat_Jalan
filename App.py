import streamlit as st

def set_background(image_file):
    """
    Menyuntikkan CSS kustom untuk mengatur gambar sebagai background aplikasi Streamlit.
    """
    # Menggunakan base64 untuk memastikan gambar dimuat dengan benar oleh CSS
    # Jika gambar berada di direktori yang sama, gunakan path 'bg.jpg'
    # Ganti 'bg.jpg' dengan nama file gambar Anda jika berbeda
    
    import base64
    with open(image_file, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{data}");
            background-size: cover;  /* Memastikan gambar menutupi seluruh background */
            background-attachment: fixed; /* Membuat gambar tetap saat menggulir */
            background-repeat: no-repeat;
        }}
        /* Menyesuaikan warna background sidebar agar tidak menutupi gambar */
        .st-emotion-cache-12fmj7 {{ /* Ini adalah class untuk sidebar Streamlit */
            background-color: rgba(30, 30, 30, 0.95); /* Sedikit transparan/gelap */
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Panggil fungsi ini di awal skrip Anda
set_background('bg.png') 

# Lanjutkan dengan kode Streamlit Anda (st.title, st.header, dll.)

st.set_page_config(page_title="Fuel Delivery System", layout="wide")

st.title("⛽ Fuel Delivery Management System")
st.markdown("""
Selamat datang di sistem pengelolaan *Fuel Order Delivery* PT. SHA SOLO.

Gunakan menu di sebelah kiri untuk:
1. Input Data DO baru  
2. Generate Surat Jalan PDF  
3. Lihat Rekap Bulanan  
4. Atur Pengaturan Sistem
""")
