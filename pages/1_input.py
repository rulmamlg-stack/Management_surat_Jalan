import streamlit as st
import pandas as pd
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm

# --- 1. Konfigurasi Path ---
DB_PATH = "dbase.xlsx"
PDF_FOLDER = "pdf_output"
ASSETS_FOLDER = "assets"
# Path untuk Header Image
HEADER_IMAGE_PATHS = [
    os.path.join(ASSETS_FOLDER, "sha.jpg"), 
    os.path.join(ASSETS_FOLDER, "header_sha.jpg"), 
    os.path.join(ASSETS_FOLDER, "header_sha.png"),
]
os.makedirs(PDF_FOLDER, exist_ok=True)
os.makedirs(ASSETS_FOLDER, exist_ok=True) 

# --- Kolom Database ---
NEW_COLUMNS = [
    "No", "Month", "SPO-Letter", "NOMOR DO", "Date", "Source", "Transportir",
    "Client", "Site/Discharge Addr Line 1", "Site/Discharge Addr Line 2",
    "PO Client", "Tgl PO", "PO Pertamina", "PIC Delivery", "Qty", "Jenis BBM",
    "Fleet Number", "Nama Driver", "Keterangan"
]

# --- 2. Fungsi Helper Database ---
@st.cache_data
def load_database(path):
    if not os.path.exists(path):
        df = pd.DataFrame(columns=NEW_COLUMNS)
        df.to_excel(path, index=False)
        return df
    else:
        df = pd.read_excel(path, engine='openpyxl') 
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce') 
        df['Tgl PO'] = pd.to_datetime(df['Tgl PO'], errors='coerce') 
        return df

def get_next_do_number(df):
    today = datetime.now()
    today_date_str = today.strftime("%d%m%y") 
    df_today = df[df['NOMOR DO'].str.startswith(today_date_str, na=False)].copy()
    
    if df_today.empty:
        next_sequence = 1
    else:
        df_today['sequence'] = df_today['NOMOR DO'].astype(str).str.split('-').str[-1]
        df_today['sequence'] = pd.to_numeric(df_today['sequence'], errors='coerce')
        max_sequence = df_today['sequence'].max()
        if pd.isna(max_sequence) or max_sequence < 1:
             next_sequence = 1
        else:
            next_sequence = int(max_sequence) + 1
            
    return f"{today_date_str}-{next_sequence:02d}"

def delete_old_data(df, do_number):
    if not do_number or do_number == "--- Buat DO Baru ---":
        st.warning("Pilih Nomor DO yang valid untuk dihapus.")
        return df
    updated_df = df[df["NOMOR DO"] != do_number].copy()
    try:
        updated_df.to_excel(DB_PATH, index=False)
        st.success(f"🗑️ Data DO **{do_number}** berhasil dihapus dari database!")
        
        # PENTING: Menghapus cache agar Streamlit memuat data terbaru
        load_database.clear() 
        
        st.session_state.do_delete_success = True
        return updated_df
    except Exception as e:
        st.error(f"Gagal menghapus data: {e}. Pastikan dbase.xlsx tidak dibuka.")
        st.session_state.do_delete_success = False
        return df


# --- 3. Fungsi Pembuat PDF (ReportLab - KOREKSI TOTAL LAYOUT) ---
def build_pdf_sha(data_row, output_path):
    # Mengatur margin menjadi sangat kecil (0.1 cm) agar KOP bisa lebar penuh
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=0.1*cm, leftMargin=0.1*cm, 
                            topMargin=0.1*cm, bottomMargin=0.1*cm) 
    
    LEBAR_PENUH_KOP = 20.8*cm
    LEBAR_KONTEN_TENGAH = 19.0*cm 
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='NormalSmall', parent=styles['Normal'], fontSize=9, leading=11)) 
    styles.add(ParagraphStyle(name='BoldSmall', parent=styles['Normal'], fontSize=9, leading=11, fontName='Helvetica-Bold')) 
    styles.add(ParagraphStyle(name='HeaderTitle', parent=styles['Normal'], fontSize=16, alignment=1, spaceAfter=2, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='FooterCenter', parent=styles['Normal'], fontSize=9, leading=11, alignment=1))
    styles.add(ParagraphStyle(name='CenterAlignSmall', parent=styles['Normal'], fontSize=9, leading=11, alignment=1))
    styles.add(ParagraphStyle(name='BeritaAcaraTitle', parent=styles['Normal'], fontSize=10, leading=12, alignment=1, fontName='Helvetica-Bold'))


    elements = []
    
    # --- Data Mapping (Clean String) ---
    do_num = str(data_row.get("NOMOR DO", ""))
    attn = str(data_row.get("PIC Delivery", ""))
    ship_to = str(data_row.get("Client", ""))
    site_addr_1 = str(data_row.get("Site/Discharge Addr Line 1", ""))
    site_addr_2 = str(data_row.get("Site/Discharge Addr Line 2", ""))
    no_po = str(data_row.get("PO Client", ""))
    # Pastikan Qty adalah float
    qty = float(data_row.get("Qty", 0.0)) if pd.notna(data_row.get("Qty")) else 0.0
    jenis_bbm = str(data_row.get("Jenis BBM", ""))
    transportir = str(data_row.get("Transportir", ""))
    fleet_no = str(data_row.get("Fleet Number", ""))
    driver = str(data_row.get("Nama Driver", ""))
    
    qty_display = f"{qty:,.0f}".replace(",", ".") # Format 16.000

    # Konversi Date
    try:
        date_obj = data_row.get("Date") if isinstance(data_row.get("Date"), datetime.date) else datetime.strptime(str(data_row.get("Date", "")), "%Y-%m-%d").date()
        date_display = date_obj.strftime("%Y-%m-%d")
    except Exception:
        date_display = str(data_row.get("Date", ""))
        
    try:
        tgl_po_obj = data_row.get("Tgl PO") if isinstance(data_row.get("Tgl PO"), datetime.date) else datetime.strptime(str(data_row.get("Tgl PO", "")), "%Y-%m-%d").date()
        tgl_po_display = tgl_po_obj.strftime("%Y-%m-%d")
    except Exception:
        tgl_po_display = str(data_row.get("Tgl PO", ""))

    
    # --- Header Gambar ---
    found_header_path = None
    for path in HEADER_IMAGE_PATHS:
        if os.path.exists(path):
            found_header_path = path
            break

    if found_header_path:
        header_img = Image(found_header_path, width=LEBAR_PENUH_KOP, height=3.5*cm) 
        elements.append(header_img)
        elements.append(Spacer(1, 2*mm)) 
    else:
        elements.append(Paragraph(f"<b>PT. SHA SOLO - [MOHON MASUKKAN GAMBAR HEADER 'sha.jpg' di folder 'assets']</b>", styles['Normal']))
        elements.append(Spacer(1, 8*mm))

    # --- Judul ---
    # KOREKSI: Mengganti LEBAR_PENUH_KONTEN_TENGAH menjadi LEBAR_KONTEN_TENGAH
    elements.append(Table([[
        Spacer(1,1),
        Paragraph("<u>FUEL ORDER DELIVERY</u>", styles['HeaderTitle']),
        Spacer(1,1)
    ]], colWidths=[(LEBAR_PENUH_KOP - LEBAR_KONTEN_TENGAH)/2, LEBAR_KONTEN_TENGAH, (LEBAR_PENUH_KOP - LEBAR_KONTEN_TENGAH)/2])) 
    elements.append(Spacer(1, 5*mm)) 
    
    # --- Info DO (Layout Rapi) ---
    LEBAR_KOLOM_KIRI = 9.0*cm 
    LEBAR_KOLOM_KANAN = 10.0*cm 
    
    # KIRI (DO #, To, Attn.)
    info_kiri_data = [
        ["DO #", Paragraph(f": <b>{do_num}</b>", styles['BoldSmall'])],
        ["To", ": PT. SHA Solo"],
        ["Attn.", Paragraph(f": <b>{attn}</b>", styles['BoldSmall'])], 
    ]
    info_kiri_table = Table(info_kiri_data, colWidths=[1.5*cm, 7.5*cm])
    info_kiri_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'), ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9), 
        ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0), 
        ('BOTTOMPADDING', (0,0), (-1,-1), 1*mm), 
    ]))
    
    # KANAN (Date, Ship To, Site, NO PO, Tgl PO, CP.)
    site_gabungan = f"<b>{site_addr_1}</b><br/><b>{site_addr_2}</b>" 
    
    info_kanan_data = [
        [Paragraph("Date", styles['NormalSmall']), ":", Paragraph(f"<b>{date_display}</b>", styles['BoldSmall'])],
        [Paragraph("Ship To", styles['NormalSmall']), ":", Paragraph(f"<b>{ship_to}</b>", styles['BoldSmall'])],
        [Paragraph("Site", styles['NormalSmall']), ":", Paragraph(site_gabungan, styles['BoldSmall'])], 
        [Paragraph("NO PO", styles['NormalSmall']), ":", Paragraph(f"<b>{no_po}</b>", styles['BoldSmall'])],
        [Paragraph("Tgl PO", styles['NormalSmall']), ":", Paragraph(f"<b>{tgl_po_display}</b>", styles['BoldSmall'])],
        [Paragraph("CP", styles['NormalSmall']), ":", ""],
    ]
    info_kanan_table = Table(info_kanan_data, colWidths=[3.5*cm, 0.2*cm, 6.3*cm])
    info_kanan_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'), ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9), 
        ('ALIGN', (0,0), (0,-1), 'RIGHT'), 
        ('ALIGN', (1,0), (1,-1), 'CENTER'), 
        ('ALIGN', (2,0), (2,-1), 'LEFT'),  
        ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0), 
        ('BOTTOMPADDING', (0,0), (-1,-1), 1*mm), 
    ]))

    info_gabungan_data = [[info_kiri_table, info_kanan_table]]
    info_gabungan_table = Table(info_gabungan_data, colWidths=[LEBAR_KOLOM_KIRI, LEBAR_KOLOM_KANAN])
    info_gabungan_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    
    spacer_width = (LEBAR_PENUH_KOP - LEBAR_KONTEN_TENGAH) / 2
    
    elements.append(Table([[
        Spacer(1,1),
        info_gabungan_table,
        Spacer(1,1)
    ]], colWidths=[spacer_width, LEBAR_KONTEN_TENGAH, spacer_width]))
    elements.append(Spacer(1, 5*mm))

    # --- Tabel Kuantitas ---
    transportir_text = Paragraph(f"<b>{transportir}</b><br/>Fleet No. <b>{fleet_no}</b><br/>An. <b>{driver}</b>", styles['BoldSmall'])
    qty_parag = Paragraph(f"<b>{qty_display}</b>", styles['HeaderTitle']) 

    items_data = [
        ["No.", "Quantity", "Description", "Diangkut Oleh Transportir"],
        ["1", qty_parag, jenis_bbm, transportir_text]
    ]
    
    items_table = Table(items_data, colWidths=[1.5*cm, 3.5*cm, 8.0*cm, 6.0*cm], rowHeights=[None, 1.8*cm])
    items_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'), ('FONTSIZE', (0,0), (-1,-1), 9), 
        ('ALIGN', (1,1), (1,1), 'CENTER'), 
        ('ALIGN', (2,1), (2,1), 'CENTER'), 
    ]))
    
    elements.append(Table([[
        Spacer(1,1),
        items_table,
        Spacer(1,1)
    ]], colWidths=[spacer_width, LEBAR_KONTEN_TENGAH, spacer_width]))
    elements.append(Spacer(1, 5*mm))

    # --- BERITA ACARA PENERIMAAN BBM / FUEL (Layout Final) ---
    
    # Header Berita Acara (Menggabungkan 4 kolom)
    header_ba_data = [
        [Paragraph("BERITA ACARA PENERIMAAN BBM / FUEL", styles['Normal'])],
        [Paragraph("Barang / BBM Solar telah di terima dan telah di periksa sebagaimana berikut :", styles['BeritaAcaraTitle'])]
    ]
    header_ba_table = Table(header_ba_data, colWidths=[LEBAR_KONTEN_TENGAH]) 
    header_ba_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
    ]))
    
    elements.append(Table([[
        Spacer(1,1),
        header_ba_table,
        Spacer(1,1)
    ]], colWidths=[spacer_width, LEBAR_KONTEN_TENGAH, spacer_width]))


    # Data Volume dikirim (Paragraf Bold)
    penerimaan_data = [
        # Col Widths: 1cm | 6.5cm | 5.75cm | 5.75cm -> Total 19.0 cm
        
        # Baris 1: Mutu Barang
        [
            Paragraph("1", styles['CenterAlignSmall']), 
            "Mutu Barang / Kualitas BBM Solar", 
            Paragraph("a. Baik", styles['CenterAlignSmall']), 
            Paragraph("b. Buruk", styles['CenterAlignSmall'])
        ], 
        # Baris 2: Volume
        [
            Paragraph("2", styles['CenterAlignSmall']), 
            Paragraph(f"Volume dikirim : <b>{qty_display}</b> Liter", styles['BoldSmall']), 
            Paragraph("Volume diterima :", styles['NormalSmall']), 
            Paragraph("............... Liter", styles['NormalSmall']),
        ], 
        # Baris 3: Segel Atas
        [
            Paragraph("3", styles['CenterAlignSmall']), 
            "Segel Atas No. ..........................", 
            Paragraph("a. Baik", styles['CenterAlignSmall']), 
            Paragraph("b. Rusak/ Terputus", styles['CenterAlignSmall'])
        ], 
        # Baris 4: Segel Bawah
        [
            Paragraph("4", styles['CenterAlignSmall']), 
            "Segel Bawah No. .......................", 
            Paragraph("a. Baik", styles['CenterAlignSmall']), 
            Paragraph("b. Rusak/ Terputus", styles['CenterAlignSmall'])
        ], 
        # Baris 5: Ketinggian T2 - KOREKSI DATA UNTUK GABUNG KOLOM 3 & 4
        [
            Paragraph("5", styles['CenterAlignSmall']), 
            "Ketinggian T2 (After Loading)", 
            Paragraph("Tepat / Lebih / Kurang (____ cm ____ ml)", styles['CenterAlignSmall']), 
            "", # Kolom kosong karena digabungkan oleh TableStyle
        ], 
    ]
    
    penerimaan_table = Table(penerimaan_data, colWidths=[1*cm, 6.5*cm, 5.75*cm, 5.75*cm]) 
    penerimaan_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black), 
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'), 
        ('FONTSIZE', (0,0), (-1,-1), 9),
        
        # Kolom No.
        ('ALIGN', (0,0), (0,-1), 'CENTER'), 

        # Kolom Deskripsi Kiri (Mutu, Segel)
        ('ALIGN', (1,0), (1,0), 'LEFT'), 
        ('ALIGN', (1,2), (1,4), 'LEFT'), 
        
        # Kolom Volume dikirim (Rata Kiri)
        ('ALIGN', (1,1), (1,1), 'LEFT'), 
        
        # Kolom Volume diterima (Label Rata Kanan, Nilai Rata Kiri)
        ('ALIGN', (2,1), (2,1), 'RIGHT'), 
        ('ALIGN', (3,1), (3,1), 'LEFT'),  
        
        # Kolom Opsi Centang (Rata Tengah)
        ('ALIGN', (2,0), (2,0), 'CENTER'), ('ALIGN', (3,0), (3,0), 'CENTER'), # Mutu
        ('ALIGN', (2,2), (2,3), 'CENTER'), ('ALIGN', (3,2), (3,3), 'CENTER'), # Segel
        
        # Ketinggian (Gabungkan Kolom 3 & 4, Rata Tengah)
        ('SPAN', (2, 4), (3, 4)), 
        ('ALIGN', (2, 4), (3, 4), 'CENTER'), 

    ]))
    
    elements.append(Table([[
        Spacer(1,1),
        penerimaan_table,
        Spacer(1,1)
    ]], colWidths=[spacer_width, LEBAR_KONTEN_TENGAH, spacer_width]))
    elements.append(Spacer(1, 3*mm))
    
    # Coment/Catatan
    elements.append(Table([[
        Spacer(1,1),
        Paragraph("<b>Coment/Catatan:</b>", styles['Normal']),
        Spacer(1,1)
    ]], colWidths=[spacer_width, LEBAR_KONTEN_TENGAH, spacer_width]))
    
    elements.append(Spacer(1, 15*mm)) 

    # --- TTD Footer ---
    
    # Peringatan 1
    elements.append(Table([[
        Spacer(1,1),
        Paragraph("BBM Solar Yang Sudah Diterima Dengan Baik Tidak Dapat Dikembalikan.", styles['FooterCenter']),
        Spacer(1,1)
    ]], colWidths=[spacer_width, LEBAR_KONTEN_TENGAH, spacer_width]))
    
    # Peringatan 2
    elements.append(Table([[
        Spacer(1,1),
        Paragraph("Tidak Menerima Keluhan Apabila BBM Solar Telah Diterima Dan Surat Jalan Telah Ditanda Tangani", styles['FooterCenter']),
        Spacer(1,1)
    ]], colWidths=[spacer_width, LEBAR_KONTEN_TENGAH, spacer_width]))
    
    elements.append(Spacer(1, 5*mm))
    
    ttd_data = [
        ["Dikirim Oleh,", "", "Diterima Oleh,"],
        ["TTD PENGANTAR", "", "TTD PENERIMA"],
        ["", "", ""], 
        ["", "", ""], 
        ["Nama dan Tanggal", "", "Nama dan Tanggal"],
    ]
    ttd_table = Table(ttd_data, colWidths=[7.5*cm, 4.0*cm, 7.5*cm])
    ttd_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('ALIGN', (2,0), (2,-1), 'CENTER'), ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10), ('LINEBELOW', (0,4), (0,4), 0.5, colors.black),
        ('LINEBELOW', (2,4), (2,4), 0.5, colors.black), ('ROWHEIGHT', (0,2), (0,3), 1*cm),
    ]))
    
    elements.append(Table([[
        Spacer(1,1),
        ttd_table,
        Spacer(1,1)
    ]], colWidths=[spacer_width, LEBAR_KONTEN_TENGAH, spacer_width]))
    
    doc.build(elements)


# --- 4. Logika Streamlit ---

# Muat data awal
df = load_database(DB_PATH) 

def init_session_state():
    if 'current_do_data' not in st.session_state:
        st.session_state['current_do_data'] = {
            "NOMOR DO": get_next_do_number(df),
            "Date": datetime.now().date(),
            "Month": datetime.now().strftime("%B"),
            "Tgl PO": datetime.now().date(),
            "Qty": 0.0,
            "Jenis BBM": "Biosolar Industri B40",
            "Transportir": "PT. SHA Solo",
            "SPO-Letter": "", "Source": "", "PO Pertamina": "", "PIC Delivery": "",
            "Fleet Number": "", "Nama Driver": "", "Keterangan": "",
            "Client": "", "Site/Discharge Addr Line 1": "", "Site/Discharge Addr Line 2": "",
            "PO Client": ""
        }

def load_old_data(df, do_number):
    if do_number and do_number != "--- Buat DO Baru ---":
        row = df[df["NOMOR DO"] == do_number].iloc[0]
        
        for key in st.session_state['current_do_data'].keys():
            if key in ['Date', 'Tgl PO']:
                val = row[key].date() if pd.notna(row[key]) and hasattr(row[key], 'date') else datetime.now().date()
            elif key == 'Qty':
                # Pastikan Qty diubah ke float
                val = float(row[key]) if pd.notna(row[key]) else 0.0
            else:
                val = str(row[key]).replace('<b>', '').replace('</b>', '').strip() if pd.notna(row[key]) else ""
                
            st.session_state['current_do_data'][key] = val
        
        st.session_state['current_do_data']['NOMOR DO'] = do_number
        st.toast(f"✅ Data DO {do_number} berhasil dipanggil! Anda bisa Edit/Cetak Ulang/Hapus.", icon="🔄")
        
def clear_inputs(df):
    # Definisi ulang data default
    clean_data = {
        "NOMOR DO": get_next_do_number(df),
        "Date": datetime.now().date(),
        "Month": datetime.now().strftime("%B"),
        "Tgl PO": datetime.now().date(),
        "Qty": 0.0,
        "Jenis BBM": "Biosolar Industri B40", 
        "Transportir": "PT. SHA Solo",
        "SPO-Letter": "", "Source": "", "PO Pertamina": "", "PIC Delivery": "",
        "Fleet Number": "", "Nama Driver": "", "Keterangan": "",
        "Client": "", "Site/Discharge Addr Line 1": "", "Site/Discharge Addr Line 2": "",
        "PO Client": ""
    }
    
    # 1. Menimpa (Overwrite) seluruh session state dengan data bersih yang baru
    st.session_state['current_do_data'] = clean_data
    
    # BARIS YANG MENYEBABKAN ERROR SUDAH DIHAPUS DI SINI.
    
    st.toast("🗑️ Form berhasil dikosongkan. Nomor DO baru siap!", icon="🎉")

init_session_state()

st.set_page_config(page_title="Input & Cetak DO", layout="wide")
st.title("📝 Input & Cetak Delivery Order")
st.markdown("Nomor DO dibuat otomatis. Anda dapat Panggil, Edit, Cetak, atau Hapus data lama.")

col_recall, col_clear, col_delete = st.columns([3, 1, 1])

with col_recall:
    do_options = ["--- Buat DO Baru ---"] + sorted(df['NOMOR DO'].dropna().unique(), reverse=True)
    selected_do = st.selectbox(
        "Panggil Data Lama",
        options=do_options,
        index=0,
        key='selected_do_key'
    )
    if st.button("🔄 Panggil Data DO"):
        load_old_data(df, selected_do)
        st.rerun() 
        
with col_clear:
    st.markdown("---") 
    if st.button("🗑️ Clear Form", width='stretch'): 
        clear_inputs(df)
        st.rerun()

with col_delete:
    st.markdown("---")
    # Tampilkan tombol Hapus hanya jika yang sedang aktif BUKAN nomor DO baru
    if st.session_state['current_do_data']['NOMOR DO'] != get_next_do_number(df):
        if st.button("❌ Hapus DO Ini", width='stretch', type='primary', help=f"Hapus DO {st.session_state['current_do_data']['NOMOR DO']} secara permanen dari Excel"):
            st.session_state.confirm_delete = True
            
if 'confirm_delete' in st.session_state and st.session_state.confirm_delete:
    st.warning(f"❗ Anda yakin ingin menghapus DO **{st.session_state['current_do_data']['NOMOR DO']}** secara permanen?")
    col_yakin, col_batal = st.columns(2)
    with col_yakin:
        if st.button("YA, Hapus Permanen", key="yakin_delete"):
            delete_old_data(df, st.session_state['current_do_data']['NOMOR DO'])
            
            # PENTING: Muat ulang database yang sudah bersih setelah penghapusan cache
            df = load_database(DB_PATH) 
            
            del st.session_state.confirm_delete
            clear_inputs(df) 
            st.rerun()
    with col_batal:
        if st.button("TIDAK, Batalkan", key="batal_delete"):
            del st.session_state.confirm_delete
            st.rerun()

st.divider()

data = st.session_state['current_do_data']

with st.form("input_form", clear_on_submit=False):
    st.subheader("1. Detail Order & Pengiriman")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.text_input("NOMOR DO", value=data["NOMOR DO"], disabled=True) 
        data["Date"] = st.date_input("Date", value=data["Date"], key='form_date') 
        data["Month"] = st.text_input("Month", value=data["Date"].strftime("%B"), key='form_month', disabled=True) 
        data["SPO-Letter"] = st.text_input("SPO-Letter", value=data["SPO-Letter"], key='form_spo')
        
    with col2:
        data["Source"] = st.text_input("Source", value=data["Source"], key='form_source')
        data["Transportir"] = st.text_input("Transportir", value=data["Transportir"], key='form_transportir') 
        data["PO Pertamina"] = st.text_input("PO Pertamina", value=data["PO Pertamina"], key='form_po_pertamina')
        data["PIC Delivery"] = st.text_input("PIC Delivery (Attn.)", value=data["PIC Delivery"], key='form_pic_delivery') 
        
    with col3:
        # Menangani nilai `None` atau non-numerik sebelum dimasukkan ke number_input
        qty_value = float(data.get("Qty", 0.0)) if pd.notna(data.get("Qty")) else 0.0
        data["Qty"] = st.number_input("Qty (Liter)", min_value=0.0, step=1.0, value=qty_value, key='form_qty') 
        data["Fleet Number"] = st.text_input("Fleet Number (Nopol)", value=data["Fleet Number"], key='form_fleet') 
        data["Nama Driver"] = st.text_input("Nama Driver", value=data["Nama Driver"], key='form_driver') 
        data["Jenis BBM"] = st.text_input("Jenis BBM (Description)", value=data["Jenis BBM"], key='form_jenis_bbm') 
        
    st.divider()
    st.subheader("2. Detail Client & PO")
    
    c1, c2 = st.columns(2)
    with c1:
        data["Client"] = st.text_input("Client (Ship To)", value=data["Client"], key='form_client') 
        data["Site/Discharge Addr Line 1"] = st.text_input("Site/Discharge Addr Line 1", value=data["Site/Discharge Addr Line 1"], key='form_site1')
        data["Site/Discharge Addr Line 2"] = st.text_input("Site/Discharge Addr Line 2", value=data["Site/Discharge Addr Line 2"], key='form_site2')

    with c2:
        data["PO Client"] = st.text_input("PO Client (NO PO.)", value=data["PO Client"], key='form_po_client') 
        data["Tgl PO"] = st.date_input("Tgl PO", value=data["Tgl PO"], key='form_tgl_po') 
        data["Keterangan"] = st.text_area("Keterangan / Catatan (Internal)", value=data["Keterangan"], key='form_keterangan')

    submitted = st.form_submit_button("💾 Simpan Data & Cetak PDF")

if submitted:
    new_data_row = st.session_state['current_do_data']
    nomor_do = new_data_row["NOMOR DO"]

    if not nomor_do or nomor_do == "--- Buat DO Baru ---":
        st.error("Error: 'NOMOR DO' tidak valid. Mohon clear input untuk mendapatkan nomor baru.")
    else:
        # PENTING: Muat ulang database (jika ada cache yang terlewat)
        load_database.clear()
        df = load_database(DB_PATH) 
        is_existing = df['NOMOR DO'].str.contains(nomor_do, na=False).any()
        
        data_to_save = new_data_row.copy()
        data_to_save["Date"] = new_data_row["Date"].strftime("%Y-%m-%d")
        data_to_save["Tgl PO"] = new_data_row["Tgl PO"].strftime("%Y-%m-%d")
        
        if is_existing:
            df_cleaned = df[~df['NOMOR DO'].str.contains(nomor_do, na=False)].copy()
            # Hindari error jika df_cleaned kosong
            next_id = df_cleaned["No"].max() + 1 if not df_cleaned.empty and df_cleaned["No"].notna().any() else 1
            data_to_save["No"] = next_id 
            
            new_row_df = pd.DataFrame([data_to_save])
            updated_df = pd.concat([df_cleaned, new_row_df], ignore_index=True)
            message = f"✅ Data DO **{nomor_do}** berhasil diperbarui (Cetak Ulang/Edit) dan disimpan ke Excel!"
        else:
            # Hindari error jika df kosong
            next_id = (df["No"].max() + 1) if not df.empty and df["No"].notna().any() else 1
            data_to_save["No"] = next_id
            
            new_row_df = pd.DataFrame([data_to_save])
            updated_df = pd.concat([df, new_row_df], ignore_index=True)
            message = f"✅ Data untuk DO **{nomor_do}** berhasil disimpan (DO Baru) ke Excel!"
        
        try:
            # Mengubah kolom Qty menjadi numeric agar tidak terjadi error saat load ulang
            updated_df['Qty'] = pd.to_numeric(updated_df['Qty'], errors='coerce')

            updated_df.to_excel(DB_PATH, index=False)
            st.success(message)
            
            safe_filename = "".join(c for c in nomor_do if c.isalnum() or c in ('-', '_')).rstrip()
            pdf_path = os.path.join(PDF_FOLDER, f"{safe_filename}.pdf")
            
            # --- PANGGIL FUNGSI PEMBUAT PDF ---
            build_pdf_sha(new_data_row, pdf_path) 
            st.success(f"✅ PDF berhasil dibuat: {pdf_path}")
            
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Surat Jalan PDF",
                    data=f,
                    file_name=os.path.basename(pdf_path),
                    mime="application/pdf"
                )
            
            # PENTING: Muat ulang database setelah menyimpan
            load_database.clear()
            df = load_database(DB_PATH) 
            
            clear_inputs(df)
            st.rerun() 
                
        except Exception as e:
            st.error(f"Terjadi error saat menyimpan: {e}")
            st.warning("Pastikan file dbase.xlsx tidak sedang dibuka di Excel.")

st.divider()
st.subheader("📋 Rekap 5 Data Terakhir")
# Pastikan ini memuat data terbaru
df_latest = load_database(DB_PATH) 
st.dataframe(df_latest.tail(5), width='stretch')
