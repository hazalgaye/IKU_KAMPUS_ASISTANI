import requests
from bs4 import BeautifulSoup
import json
import time

def veri_topla():
    print("İKÜ Veri Çekme İşlemi Başlatılıyor")
    
    hedefler = [
        {
            "kategori": "ulasim",
            "url": "https://www.iku.edu.tr/tr/ikuye-kara-yolu-ile-ulasim",
            "etiket": ["p", "div", "li"],
            "tur": "Ulaşım Bilgileri"
        },
        {
            "kategori": "sss",
            "url": "https://oidb.iku.edu.tr/tr/sss",
            "etiket": ["h4", "h5", "div", "p"], 
            "tur": "Sıkça Sorulan Sorular"
        },
        {
            "kategori": "erasmus",
            "url": "https://aday.iku.edu.tr/erasmus",
            "etiket": ["p", "li", "div", "h3", "h4"], 
            "tur": "Erasmus Olanakları"
        },
        {
            "kategori": "kampus",
            "url": "https://aday.iku.edu.tr/yerleskeler",
            "etiket": ["p", "h3", "div"],
            "tur": "Yerleşkeler"
        },
        {
            "kategori": "burslar",
            "url": "https://aday.iku.edu.tr/burslar-ve-indirimler",
            "etiket": ["p", "li"],
            "tur": "Burslar ve İndirimler"
        },
        {
            "kategori": "yurtlar",
            "url": "https://www.iku.edu.tr/tr/istanbul-kultur-universitesi-yurtlari",
            "etiket": ["p", "li", "div"],
            "tur": "Yurt Olanakları"
        }
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    toplanan_veri = {}

    for hedef in hedefler:
        print(f"📡 {hedef['tur']} taranıyor...")
        try:
            response = requests.get(hedef['url'], headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                temiz_liste = []
                for tag in hedef['etiket']:
                    bulunanlar = soup.find_all(tag)
                    for veri in bulunanlar:
                        metin = veri.get_text(strip=True)
                        if len(metin) > 25 and "Copyright" not in metin and "Menü" not in metin:
                            temiz_liste.append(metin)
                toplanan_veri[hedef['kategori']] = list(set(temiz_liste))
                print(f" BAŞARILI! {len(toplanan_veri[hedef['kategori']])} veri çekildi.")
            else:
                print(f" HATA: Sayfa açılmadı ({response.status_code})")
        except Exception as e:
            print(f"HATA: {e}")
        time.sleep(1)

    # Dosyayı kaydet
    dosya_adi = "bilgi_bankasi2.json"
    print("-" * 60)
    with open(dosya_adi, 'w', encoding='utf-8') as f:
        json.dump(toplanan_veri, f, ensure_ascii=False, indent=4)
        print(f"İşlem bitti. Veriler '{dosya_adi}' dosyasına kaydedildi.")

if __name__ == "__main__":
    veri_topla()