import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urljoin
import re

# 1. AYARLAR & API
st.set_page_config(
    page_title="İKÜ Kampüs Asistanı", 
    page_icon="https://www.iku.edu.tr/sites/default/files/favicons/favicon.ico")

API_KEY = "API KEYI BURAYA YAZIN" 

try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash') 
except Exception as e:
    st.error(f"API Hatası: {e}")

# 2. ETKİNLİK ÇEKME MODÜLLERİ 

UA = {'User-Agent': 'Mozilla/5.0'} 

def unical_cek():
    base = "https://unical.iku.edu.tr"
    list_url = base + "/cal/main/showMainEnd.rdo"

    s = requests.Session()
    r = s.get(list_url, headers=UA, timeout=10)
    if r.status_code != 200:
        return ""

    soup = BeautifulSoup(r.text, "html.parser")
    sonuc = []

    for a in soup.select('a[href*="eventView.do"]'):
        etkinlik_adi = a.get_text(" ", strip=True)
        href = a.get("href")

        if not etkinlik_adi or not href:
            continue

        link = urljoin(base, href)

        d = s.get(link, headers=UA, timeout=10)
        if d.status_code != 200:
            continue

        detay = BeautifulSoup(d.text, "html.parser")
        text = detay.get_text("\n", strip=True)

        saat = "Saat bilgisi yok"
        m_saat = re.search(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", text)
        if m_saat:
            saat = m_saat.group(1) + " - " + m_saat.group(2)

        tarih = "Tarih bilgisi yok"
        m_tarih = re.search(r"Zaman:\s*(.+)", text)
        if m_tarih:
            tarih = m_tarih.group(1)

        yer = "Yer bilgisi yok"
        m_yer = re.search(r"Nerede:\s*(.+)", text)
        if m_yer:
            yer = m_yer.group(1)

        sonuc.append(
            f"""
Etkinlik Adı: {etkinlik_adi}
Tarih: {tarih}
Saat: {saat}
Yer: {yer}
"""
        )

    return "\n".join(sonuc)


def kultur_ajandasi_cek():
    base = "https://www.iku.edu.tr"
    list_url = base + "/tr/etkinlikler"

    s = requests.Session()
    r = s.get(list_url, headers=UA, timeout=15)
    if r.status_code != 200:
        return ""

    soup = BeautifulSoup(r.text, "html.parser")
    sonuc = []

    for a in soup.find_all("a", href=True):
        etkinlik_adi = a.get_text(" ", strip=True)
        href = a["href"]

        if not etkinlik_adi or len(etkinlik_adi) < 3:
            continue
        if not href.startswith("/tr/") or href == "/tr/etkinlikler":
            continue

        link = urljoin(base, href)

        d = s.get(link, headers=UA, timeout=15)
        if d.status_code != 200:
            continue

        detay = BeautifulSoup(d.text, "html.parser")
        text = detay.get_text("\n", strip=True)

        saat = "Saat bilgisi yok"
        m_saat = re.search(r"(\d{1,2}[.:]\d{2})\s*-\s*(\d{1,2}[.:]\d{2})", text)
        if m_saat:
            saat = m_saat.group(1) + " - " + m_saat.group(2)

        tarih = "Tarih bilgisi yok"
        m_tarih = re.search(r"\d{1,2}\s+[A-Za-zÇĞİÖŞÜçğıöşü]+\s+\d{4}", text)
        if m_tarih:
            tarih = m_tarih.group(0)

        yer = "Yer bilgisi yok"
        m_yer = re.search(r"(Yer|Mekan|Konum)\s*:\s*(.+)", text, re.IGNORECASE)
        if m_yer:
            yer = m_yer.group(2)

        sonuc.append(
            f"""
Etkinlik Adı: {etkinlik_adi}
Tarih: {tarih}
Saat: {saat}
Yer: {yer}
"""
        )

    return "\n".join(sonuc)

# 3. BİLGİ BANKASI VE REHBERLİK MODÜLÜ 

def bilgi_bankasi_yukle():
    """
    Statik olarak hazırlanan 'bilgi_bankasi.json' verileri ile 
    web scraping yöntemiyle çekilen 'bilgi_bankasi2.json' verilerini okur ve birleştirir.
    """
    tum_veriler = {}

    if os.path.exists("bilgi_bankasi2.json"):
        try:
            with open("bilgi_bankasi2.json", "r", encoding="utf-8") as f:
                tum_veriler.update(json.load(f))
        except: pass

    if os.path.exists("bilgi_bankasi.json"):
        try:
            with open("bilgi_bankasi.json", "r", encoding="utf-8") as f:
                el_verisi = json.load(f)
                for anahtar, deger in el_verisi.items():
                    if anahtar in tum_veriler and isinstance(deger, list) and isinstance(tum_veriler[anahtar], list):
                        tum_veriler[anahtar] = deger + tum_veriler[anahtar]
                    else:
                        tum_veriler[anahtar] = deger
        except:
            return "Manuel bilgi bankası okunurken hata oluştu."
    
    if not tum_veriler:
        return "Bilgi bankası dosyaları bulunamadı."

    return json.dumps(tum_veriler, ensure_ascii=False, indent=2)

@st.cache_data(ttl=3600, show_spinner=False)
def tum_verileri_hazirla():
    veri_unical = unical_cek()
    veri_ajanda = kultur_ajandasi_cek()
    veri_rehber = bilgi_bankasi_yukle()
    
    
    sistem_bilgisi = f"""
    === 1. CANLI ETKİNLİK VERİLERİ (ÖNCELİKLİ) ===
    {veri_unical}
    
    === 2. WEB SİTESİ ETKİNLİKLERİ ===
    {veri_ajanda}
    
    === 3. KAMPÜS BİLGİ BANKASI (BÖLÜMLER, KULÜPLER, TÜYOLAR) ===
    {veri_rehber}
    """
    return sistem_bilgisi, "Veri kaynakları aktif."
    
#  ARAYÜZ VE SOHBET 

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Selam! 👋 **İKÜ Kampüs Asistanı** seninle!\n\n📅 **Etkinlikleri** anlık takip ediyorum.\n🎓 **Bölüm önerisi** ve **Burs** bilgileri bende.\n🍕 **Kantin, Yemek ve Kampüs Tüyoları** verebilirim.\n\nNasıl yardımcı olabilirim?"
    })

with st.sidebar:
    st.image("Logo.png", width=150)
    st.markdown("### 🌟 Neler Yapabilirim?")
    st.info("• 'Teknoloji ilgi alanı için etkinlik öner.'\n• 'Yarın ne etkinlik var?'\n• 'Kampüs tüyosu ver.'\n• 'İncirli kampüsü nasıl?'\n• 'Burs imkanları neler?'")
    
    if st.button("Sohbeti Temizle 🗑️"):
        st.session_state.messages = []
        st.rerun()

st.title("🎓 İKÜ Kampüs Asistanı")
st.caption("🚀 Etkinlik Takvimi & Öğrenci Rehberi")
st.markdown("---")
if "user_type" not in st.session_state:
    st.markdown("### Hoş Geldin! 👋 \nSana daha iyi yardımcı olabilmem için lütfen durumunu seçer misin?")
    col1, col2 = st.columns(2)
    
    if col1.button("🎓 İKÜ Öğrencisiyim", use_container_width=True):
        st.session_state.user_type = "İKÜ Öğrencisi"
        # İlk mesajı özelleştirilmiş
        st.session_state.messages.append({"role": "assistant", "content": "Harika! Bir İKÜ'lü olarak sana CATS, PUMA, derslikler veya kampüs tüyoları hakkında yardımcı olabilirim. Ne bilmek istersin?"})
        st.rerun()
        
    if col2.button("🌟 Aday Öğrenciyim", use_container_width=True):
        st.session_state.user_type = "Aday Öğrenci"
        st.session_state.messages.append({"role": "assistant", "content": "Hoş geldin! İKÜ ailesine katılman bizi mutlu eder. Sana bölümler, burs imkanları, kampüs olanakları ve kayıt süreçleri hakkında bilgi verebilirim. Neyi merak ediyorsun?"})
        st.rerun()
    
    st.stop()
st.sidebar.info(f"Kullanıcı Modu: {st.session_state.user_type}")


for mesaj in st.session_state.messages:
    role = "user" if mesaj["role"] == "user" else "assistant"
    with st.chat_message(role):
        st.markdown(mesaj["content"])

prompt = st.chat_input("Sorunuzu buraya yazın...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    #  Kullanıcı mesajını göster
    with st.chat_message("user"):
        st.markdown(prompt)

    # Asistan cevabı üret + göster
    with st.chat_message("assistant"):
        with st.spinner("Bilgiler taranıyor... 🧠"):

            tum_veri, sistem_durumu = tum_verileri_hazirla() 

            try:
                system_instruction = f"""
                Sen İstanbul Kültür Üniversitesi (İKÜ) Akıllı Asistanısın.
                
                ELİNDEKİ VERİLER:
                {tum_veri}
                ŞU AN KONUŞTUĞUN KİŞİ: {st.session_state.user_type}
                
                GÖREVİN:
                Öğrencinin sorusunu analiz et ve elindeki verilere göre EN YARARLI cevabı ver.
                
                --- KESİN KURALLAR ---
                
                1. GİZLİLİK: Verinin kaynağını (JSON, Unical vb.) asla söyleme.Tüm etkinlikleri tek bir takvimden geliyormuş gibi sun.

                2. İLK TEPKİ KURALI (Doğal Başlangıç):
                   - Eğer kullanıcı sadece SELAM verirse veya genel bir soru sorarsa, nazikçe cevap ver ve "Nasıl yardımcı olabilirim?" diye sor.

                3. ETKİNLİKLER (UNUTMA!):
                   - Kullanıcı etkinlik sorarsa 1. ve 2. veri kaynaklarındaki (Canlı) etkinlikleri tarih/saat belirterek listele.

                4. İLGİ ALANI SORGULAMA KURALI:
                   - Eğer kullanıcı "etkinlik öner", "kulüp öner", "ne var" gibi net bir şekilde öneri isterse, hemen şunu sor: **"Hangi alanda etkinlik/kulüp istersin? (Örn: Müzik, yazılım, spor, sanat?)"**
                
                5. DİNAMİK ÖNERİ KURALI:
                   - Kullanıcı ilgi alanı belirttikten sonra:
                   - Eğer kullanıcı özellikle **KULÜP** isterse: Yalnızca kulübü ve özelliklerini öner.
                   - Eğer kullanıcı özellikle **ETKİNLİK** isterse: Yalnızca ilgi alanına uyan, **filtrelenmiş** etkinlikleri listele.
                   - Eğer kullanıcı hem kulüp hem etkinlik isterse VEYA genel olarak "ne yapabilirim" derse: Her ikisini de öner. Kulübün **'ad'ını ve 'özellik'** detayını kullanarak öneri yap.
                   - AYRICA: Eğer kullanıcı direkt kulübün adını sorarsa (örn: "Asimov ne yapar?"), **'özellik'** detayını eksiksiz olarak anlat.
                
                6. ÖZEL KAMPÜS TÜYOLARI (YEMEK/KAHVE/DERS):
                   - **BURASI ÇOK ÖNEMLİ:** Kullanıcı "Kantin nasıl?", "Yemek nerede yenir?", "Ders çalışılır mı?" diye sorduğunda GENEL CEVAP VERME.
                   - Mutlaka 'kantin_ve_yemek_tuyolari', 'gizli_ders_calisma_yerleri' listelerindeki **ÖZEL DETAYLARI** kullan.
                   - Örnek: "Yemekhane 12'de kalabalıktır", "Çetin Abi'nin makarnası meşhurdur", "Ataköy Starbucks sırası uzundur", "Termosunu getir" gibi veride yazan detayları söyle.
                
                7. BÖLÜM TAVSİYESİ VE İLGİ ALANI:
                   - "Hangi bölümü seçeyim?" derse ilgi alanını sor. İlgi alanına göre veri bankasındaki bölümleri eşleştirip öner.
                   - "Bilgisayar Programcılığı nasıl?" gibi spesifik bölüm sorularında JSON'daki **ÖZEL NOTLARI** (Örn: Erdem Hoca, vizyonerlik, dersleri kaçmaz, laboratuvar imkanları) mutlaka anlat.
                
                8. BURSLAR, YURTLAR VE YERLEŞKELER:
                   - Burs oranları, yurt imkanları ve yerleşke konumları hakkında veride ne varsa detaylı aktar.

                9. SİSTEMLER VE TEKNİK REHBER (CATS/PUMA/ORION):
                   - Kullanıcı CATS, PUMA veya ORION hakkında soru sorarsa (şifre, giriş, yemek listesi vb.), 'sistem_rehberi' verisindeki bilgileri kullanarak adım adım ne yapması gerektiğini anlat.
                
                10. ÜSLUP: 
                   - Samimi, yardımsever ve öğrenci dostu ol. "Çetin Abi'ye selam söyle" gibi notlar varsa onları da ilet.
                   - Veride olmayan bir şeyi uydurma.

                11.KULLANICI ÖZELLEŞTİRME:
                    - Eğer karşındaki bir 'Aday Öğrenci' ise; Burslar, bölümler, kampüs yaşamı verilere odaklan ve onu üniversiteye özendirici, sıcak bir dil kullan.
                    - Eğer karşındaki bir 'İKÜ Öğrencisi' ise; CATS, PUMA/ORION , Kampüs tüyoları , etkinlikler gibi teknik ve kampüs içi verilere odaklan.

                """

                chat_history = []
                for m in st.session_state.messages:
                    role = "user" if m["role"] == "user" else "model"
                    chat_history.append({"role": role, "parts": [m["content"]]})

                chat = model.start_chat(history=chat_history)
                response = chat.send_message(system_instruction + "\n\nKullanıcı Sorusu: " + prompt)

                bot_cevabi = response.text

                st.markdown(bot_cevabi)

                st.session_state.messages.append({"role": "assistant", "content": bot_cevabi})

                st.rerun()

            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "content": f"Hata oluştu: {e}"})
                st.rerun()
