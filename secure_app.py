import os
import secrets
import logging
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import secrets
from werkzeug.exceptions import BadRequest
import bleach  # XSS temizleme
from functools import wraps

# Güvenlik kütüphaneleri
from flask_wtf.csrf import CSRFProtect, generate_csrf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import threading

# Güvenlik konfigürasyonu
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
MAX_CONTENT_LENGTH = 1024 * 1024  # 1MB limit
PERMITTED_USER_AGENTS = [
    'Mozilla/5.0', 'Chrome/', 'Safari/', 'Edge/'
]

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['TRAP_BAD_REQUEST_ERRORS'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=12*60*60)

# Rate limiting (saldırı önleme)
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# CSRF koruması
csrf = CSRFProtect(app)

# HTTP Security Headers (OWASP Top 10 koruması)
csp = {
    'default-src': "'self'",
    'script-src': "'self'",
    'style-src': "'self' 'unsafe-inline'",
    'img-src': "'self' data: https:",
    'connect-src': "'self' http://localhost:5000"
}
talisman = Talisman(
    app,
    content_security_policy=csp,
    strict_transport_security=True,
    force_https=False,  # Production'da True yapın
    frame_options='DENY',
    x_content_type_options=True
)

# Güvenlik loglama
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class SecureStatsCollector:
    def __init__(self):
        self.cache = {}
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
    
    def sanitize_input(self, data):
        """XSS ve injection koruması"""
        if isinstance(data, str):
            return bleach.clean(data, tags=[], strip=True)
        return data
    
    def validate_request(self, league):
        """İzin verilen ligler"""
        valid_leagues = ['superlig', 'bundesliga', 'premier', 'saudi']
        if league not in valid_leagues:
            abort(400, description=f"Geçersiz lig. İzinliler: {valid_leagues}")
        return True
    
    def check_user_agent(self):
        """Bot trafiği engelleme"""
        ua = request.headers.get('User-Agent', '').lower()
        suspicious = any(keyword in ua for keyword in ['bot', 'crawler', 'spider', 'scan'])
        if suspicious or len(ua) < 10:
            abort(403, description="Erişim engellendi")
    
    def rate_limit_cache(self, key):
        """Cache poisoning önleme"""
        if key in self.cache and time.time() - self.cache[key]['timestamp'] < 3600:  # 1 saat
            return self.cache[key]['data']
        return None

collector = SecureStatsCollector()

'''def security_wrapper(f):
    """Tüm endpoint'ler için güvenlik katmanı"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Rate limiting
        if not limiter.check_request_limit():
            abort(429, description="Çok fazla istek")
        
        # User-Agent kontrol
        collector.check_user_agent()
        
        # Input sanitization
        for key in request.args:
            request.args[key] = collector.sanitize_input(request.args[key])
        
        # CSRF token kontrolü
        if request.method == 'POST':
            csrf_token = request.headers.get('X-CSRF-Token')
            if not csrf_token:
                abort(403, description="CSRF token gerekli")
        
        return f(*args, **kwargs)
    return decorated_function
'''
def security_wrapper(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ua = request.headers.get('User-Agent', '')
        if not any(x in ua for x in PERMITTED_USER_AGENTS):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
    
@app.errorhandler(400)
def bad_request(e):
    return jsonify({'error': 'Geçersiz istek'}), 400

@app.errorhandler(403)
def forbidden(e):
    return jsonify({'error': 'Erişim engellendi'}), 403

@app.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify({'error': 'Çok fazla istek, lütfen bekleyin'}), 429

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Sunucu hatası'}), 500

@app.route('/health')
@limiter.limit("10 per minute")
def health_check():
    return jsonify({
        'status': 'OK', 
        'timestamp': datetime.now().isoformat(),
        'version': '2.0-secure'
    })

@app.route('/api/stats/<league>', methods=['GET'])
@limiter.limit("10 per minute")
@security_wrapper
def get_league_stats(league):
    """🔒 GÜVENLİ lig istatistikleri"""
    league = collector.sanitize_input(league.lower())
    collector.validate_request(league)
    
    limit = int(request.args.get('limit', 50))
    if limit > 100 or limit < 1:
        abort(400, description="Limit 1-100 arası olmalı")
    
    cache_key = f"{league}_{limit}"
    cached = collector.rate_limit_cache(cache_key)
    if cached:
        return jsonify(cached)
    
    print(f"📊 {league.upper()} güvenli veri çekiliyor...")
    
    # Scraping kodunuz buraya (önceki AdvancedStatsCollector)
    stats = []  # collector.get_detailed_stats(league)  # Mevcut kodunuz
    stats = [
        {'oyuncu': 'Mauro Icardi', 'performans_skoru': 92, 'takim': 'Galatasaray'},
        {'oyuncu': 'Edin Dzeko', 'performans_skoru': 88, 'takim': 'Fenerbahçe'},
        {'oyuncu': 'Gedson Fernandes', 'performans_skoru': 85, 'takim': 'Beşiktaş'}
    ]
    
 #   if not stats:
 #       return jsonify({'error': f'{league.upper()} verisi alınamadı'}), 503
    if not stats:
        return jsonify({
        'lig': league.upper(),
        'oyuncular': [],
        'mesaj': 'Henüz veri çekilmedi, scraping fonksiyonunu bağlayın.'
        })
    
    df = pd.DataFrame(stats)
    top_players = df.nlargest(limit, 'performans_skoru').to_dict('records')
    
    result = {
        'lig': league.upper(),
        'toplam_oyuncu': len(df),
        'limit': limit,
        'timestamp': datetime.now().isoformat(),
        'oyuncular': top_players[:limit]
    }
    
    collector.cache[cache_key] = {'data': result, 'timestamp': time.time()}
    return jsonify(result)

@app.route('/api/keepers/<league>', methods=['GET'])
@limiter.limit("5 per minute")
@security_wrapper
def get_keepers(league):
    """🔒 Kaleci istatistikleri"""
    league = collector.sanitize_input(league.lower())
    collector.validate_request(league)
    return jsonify({'kaleciler': []})  # Mevcut kodunuz

@app.route('/api/compare', methods=['GET'])
@limiter.limit("3 per minute")
@security_wrapper
def compare_leagues():
    """🔒 Lig karşılaştırması"""
    leagues = request.args.getlist('ligler[]')
    for lig in leagues:
        collector.validate_request(lig.lower())
    return jsonify({})

# API Key koruması (opsiyonel)
API_KEYS = set(['demo-key-123'])  # Production'da environment variable

@app.before_request
def require_api_key():
    if not any(request.path.startswith(p) for p in ['/health']):
        api_key = request.headers.get('X-API-Key')
        if api_key not in API_KEYS:
            abort(401, description="API Key gerekli")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)  # ← 127.0.0.1 YASAK!
    