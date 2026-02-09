Kurulum-çalıştırma
# Gerekli kütüphaneler
pip install flask flask-cors pandas beautifulsoup4 selenium lxml requests openpyxl

# ChromeDriver indirin ve PATH'e ekleyin
# Linux: sudo apt install chromium-chromedriver
# Mac: brew install chromedriver

# Servisi başlatın
python app.py

API Kullanım Örnekleri
# Tek lig istatistikleri
curl "http://localhost:5000/api/stats/superlig?limit=20"

# Premier League
curl "http://localhost:5000/api/stats/premier?limit=10"

# Kaleciler
curl "http://localhost:5000/api/keepers?lig=bundesliga"

# Lig karşılaştırması
curl "http://localhost:5000/api/compare?ligler[]=superlig&ligler[]=premier"

# Health check
curl "http://localhost:5000/health"

Örnek json çıktısı
{
  "lig": "SUPERLIG",
  "toplam_oyuncu": 245,
  "oyuncular": [
    {
      "oyuncu": "Victor Osimhen",
      "pozisyon": "FW",
      "gol": 12,
      "asist": 3,
      "xg": 10.2,
      "pas_yuzde": "78.4%",
      "tackles": 1.2,
      "performans_skoru": 42.8
    },
    {
      "oyuncu": "Neuer",
      "pozisyon": "GK",
      "kurtaris": 85,
      "kurtaris_yuzde": "82.1%",
      "gol_yeme_90": 0.89,
      "performans_skoru": 38.4
    }
  ]
}

Docker production, dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y chromium chromium-driver
EXPOSE 5000
CMD ["python", "app.py"]

✅ Özellikler:

Pas yüzdeleri, top kapmalar, kurtarışlar, gol yeme/90
30dk cache ile hızlı yanıt
4 lig desteği
Kaleci özel endpoint
Lig karşılaştırma
Production-ready Flask
Servis hazır! Test etmek için curl komutlarını kullanabilirsin.


Örnek python kodları çalışma testi için 
# 1. Lig istatistikleri (DETAYLI METRİKLER İLE)
GET /api/stats/superlig?limit=20  # Pas%, Tackles, Saves, xG, GA90
GET /api/stats/bundesliga?limit=10
GET /api/stats/premier?limit=10  
GET /api/stats/saudi?limit=10

# 2. Kaleciler özel (kurtarış, gol yeme ortalaması)
GET /api/keepers?lig=superlig
GET /api/keepers?lig=bundesliga

# 3. Lig karşılaştırması
GET /api/compare?ligler[]=superlig&ligler[]=premier&ligler[]=bundesliga

# 4. Health check
GET /health

Test scriptleri
# 1. Süper Lig TOP 20 oyuncu (gol, asist, pas%, tackles, kurtarış)
curl "http://localhost:5000/api/stats/superlig?limit=20"

# 2. Premier League en iyiler
curl "http://localhost:5000/api/stats/premier?limit=5"

# 3. Bundesliga kaleciler
curl "http://localhost:5000/api/keepers?lig=bundesliga"

# 4. 3 lig karşılaştırması
curl "http://localhost:5000/api/compare?ligler[]=superlig&ligler[]=premier&ligler[]=bundesliga"

app.py dosyasını:

✅ pip install flask flask-cors pandas beautifulsoup4 selenium lxml

✅ ChromeDriver kur

✅ python app.py

✅ Yukarıdaki curl komutları ile test et

secure_app.py dosyasını
Güvenlik Özellikleri (OWASP Top 10 Korumalı)
Tehdit	Koruma	Kodda
Injection	Input sanitization + bleach	sanitize_input()
XSS	CSP + bleach.clean()	Talisman + bleach
CSRF	CSRF token zorunlu	flask_wtf.csrf
Rate Limit	IP bazlı limit	flask_limiter
Clickjacking	X-Frame-Options	Talisman
MIME Sniffing	X-Content-Type	Talisman
Bot Saldırıları	User-Agent filtre	check_user_agent()
Cache Poisoning	Timestamp kontrol	rate_limit_cache()

Güvenli Kurulum
pip install flask flask-cors flask-limiter flask-talisman flask-wtf bleach pandas beautifulsoup4 selenium lxml

# Environment variable
export SECRET_KEY="your-64-char-secret-key-here"
export API_KEY="your-api-key"

# Sadece localhost çalıştır
python secure_app.py

production deploy
# nginx.conf - Örnek
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;
    
    location /api/ {
        limit_req zone=api burst=20;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header X-API-Key $http_x_api_key;
    }
}

Güvenli test
# API Key ile
curl -H "X-API-Key: demo-key-123" "http://localhost:5000/api/stats/superlig?limit=10"

# Hatalı istek test
curl "http://localhost:5000/api/stats/invalid"  # 400 dönecek

