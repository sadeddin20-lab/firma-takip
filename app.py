import streamlit as st
import gspread
import pandas as pd
from datetime import datetime

# Sayfa Ayarları
st.set_page_config(page_title="ELÇİ OSGB - Firma Takip", layout="wide")

def main():
    st.markdown("## 🏢 ELÇİ OSGB - FİRMA TAKİP SİSTEMİ")
    
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.is_admin = False
        if "users" not in st.session_state:
            st.session_state.users = {"elci": "osgb2026", "admin": "sadoreis"}

    if not st.session_state.logged_in:
        st.subheader("🔑 Giriş Paneli")
        username = st.text_input("Kullanıcı Adı")
        password = st.text_input("Şifre", type="password")
        if st.button("Giriş Yap"):
            if username in st.session_state.users and st.session_state.users[username] == password:
                st.session_state.logged_in = True
                st.session_state.is_admin = (username == "admin")
                st.rerun()
            else:
                st.error("Kullanıcı adı veya şifre hatalı!")
        return

    try:
        gc = gspread.service_account(filename='credentials.json')
        sh = gc.open_by_key("1RCmzZcmeGzru3J-kSfqBL-TPPFJV6nnJTCWT69vxTrA").sheet1
        data = sh.get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
    except Exception as e:
        st.error(f"Veri bağlantısı hatası: {e}")
        return

    if st.session_state.is_admin:
        with st.sidebar.expander("👑 Yönetici Paneli"):
            st.subheader("Yeni Firma Ekle")
            yeni_firma = st.text_input("Firma Adı")
            if st.button("Firma Kaydı Oluştur"):
                sh.append_row([""] * 12 + [yeni_firma])
                st.rerun()
            st.subheader("Yeni Kullanıcı")
            new_user = st.text_input("Yeni Kullanıcı Adı")
            new_pass = st.text_input("Yeni Şifre", type="password")
            if st.button("Kullanıcıyı Kaydet"):
                st.session_state.users[new_user] = new_pass
                st.success(f"Kullanıcı {new_user} eklendi!")

    if "selected_firm_idx" in st.session_state:
        idx = st.session_state.selected_firm_idx
        row = df.iloc[idx]
        st.subheader(f"🏢 {row.iloc[12]}")
        
        col_n, col_p, col_r = st.columns(3)
        col_n.caption("SGK Sicil Numarası")
        col_n.write(f"**{row.iloc[13]}**")
        col_p.caption("Çalışan Sayısı")
        col_p.write(f"**{row.iloc[15]}**")
        col_r.caption("Sözleşme Onay Tarihi")
        col_r.write(f"**{row.iloc[17]}**")
        
        st.write("---")
        st.subheader("📋 Evrak ve Ziyaret Durum Tablosu")

        for i in range(19, 30):
            col_name = df.columns[i]
            c1, c2, c3, c4 = st.columns([2, 1, 3, 1])
            c1.write(f"**{col_name}**")
            
            # Ziyaret (24) ve İletişim (25) için radio butonları kaldırdık
            if i not in [24, 25]:
                durum = c2.radio(f"D_{i}", ["✅", "❌"], index=0 if row.iloc[i] == "✅" else 1, key=f"d_{i}", label_visibility="collapsed")
            else:
                c2.empty() # Radio butonlarını kaldırdık
            
            if i == 25: # Z Sütunu (İletişim)
                yeni_tel = c3.text_input("İletişim/Tel", value=row.iloc[i], key=f"t_{i}", label_visibility="collapsed")
                if c4.button("Kaydet", key=f"btn_{i}"):
                    sh.update_cell(idx + 2, i + 1, yeni_tel)
                    st.success("İletişim güncellendi!")
            elif i == 24: # Y Sütunu (Ziyaret Tarihleri)
                yeni_tarih = c3.date_input("Ziyaret Tarihi", key=f"date_{i}")
                if c4.button("Ekle", key=f"add_{i}"):
                    mevcut = str(row.iloc[i])
                    guncel = f"{mevcut}, {yeni_tarih}" if mevcut and mevcut != "nan" else str(yeni_tarih)
                    sh.update_cell(idx + 2, i + 1, guncel)
                    st.rerun()
            else:
                c3.text_input("Not", key=f"n_{i}", label_visibility="collapsed")
                if c4.button("Kaydet", key=f"btn_{i}"):
                    sh.update_cell(idx + 2, i + 1, durum)
                    st.success("Güncellendi!")

        if st.button("⬅️ Listeye Dön"): del st.session_state.selected_firm_idx; st.rerun()
            
    else:
        st.title("Firma Listesi")
        tehlike_sinifi = st.selectbox("Tehlike Sınıfı Seç:", df.iloc[:, 16].unique())
        for i, row in df[df.iloc[:, 16] == tehlike_sinifi].iterrows():
            if st.button(f"Firma: {row.iloc[12]}", key=f"btn_{i}"):
                st.session_state.selected_firm_idx = i
                st.rerun()

if __name__ == "__main__":
    main()
