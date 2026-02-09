from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import threading
import json
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Frontend entegrasyonu için

class AdvancedStatsCollector:
    def __init__(self):
        self.cache = {}
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
    
    def get_detailed_stats(self, league):
        """Detaylı istatistikler: Pas%, Tackles, Saves, Clean Sheets"""
        league_configs = {
            'superlig': {'fbref': 'https://fbref.com/en/comps/203/2025/gca/Trendyol-Super-Lig-Stats', 'whoscored': 'Turkey-Super-Lig'},
            'bundesliga': {'fbref': 'https://fbref.com/en/comps/20/2025/gca/Bundesliga-Stats', 'whoscored': 'Germany-Bundesliga'},
            'premier': {'fbref': 'https://fbref.com/en/comps/9/2025/gca/Premier-League-Stats', 'whoscored': 'England-Premier-League'},
            'saudi': {'fbref': 'https://fbref.com/en/comps/83/2025/gca/Saudi-Pro-League-Stats', 'whoscored': 'Saudi-Pro-League'}
        }
        
        config = league_configs.get(league)
        if not config:
            return []
        
        stats = []
        
        # FBref - En detaylı istatistik kaynağı
        try:
            fbref_data = self.scrape_fbref_detailed(config['fbref'])
            stats.extend(fbref_data)
            time.sleep(1)
        except:
            pass
        
        # WhoScored ek metrikler
        try:
            whoscored_data = self.scrape_whoscored_advanced(config['whoscored'])
            stats.extend(whoscored_data)
        except:
            pass
        
        return stats
    
    def scrape_fbref_detailed(self, url):
        """FBref: xG, Pass%, Tackles, Interceptions, Saves, PSxG"""
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        players = []
        # Standart oyuncu istatistikleri
        for row in soup.select('table#stats_standard tbody tr'):
            cells = row.find_all('td')
            if len(cells) >= 20:
                name = cells[1].find('a').text.strip()
                pos = cells[2].text.strip()
                team = cells[0].text.strip()
                
                # İstatistikler (sütun indeksleri FBref yapısına göre)
                minutes = cells[12].text
                goals = cells[14].text
                assists = cells[15].text
                xg = cells[20].text
                pass_pct = cells[18].text  # Pas yüzdesi
                
                players.append({
                    'lig': 'FBref',
                    'oyuncu': name,
                    'pozisyon': pos,
                    'takim': team,
                    'dakika': minutes,
                    'gol': goals,
                    'asist': assists,
                    'xg': xg,
                    'pas_yuzde': pass_pct,
                    'kaynak': 'FBref-Standard'
                })
        
        # Savunma istatistikleri (ayrı tablo)
        defense_table = soup.select('table#stats_defense tbody tr')
        for row in defense_table[:50]:  # İlk 50 oyuncu
            cells = row.find_all('td')
            if len(cells) >= 10:
                name = cells[1].find('a').text.strip()
                tackles = cells[6].text
                interceptions = cells[7].text
                
                # Mevcut oyuncuya ekle
                for player in players:
                    if player['oyuncu'] == name:
                        player['tackles'] = tackles
                        player['interceptions'] = interceptions
                        break
        
        # Kaleci istatistikleri
        keeper_table = soup.select('table#stats_keeper tbody tr')
        for row in keeper_table:
            cells = row.find_all('td')
            if len(cells) >= 15:
                name = cells[1].find('a').text.strip()
                saves = cells[10].text
                save_pct = cells[11].text
                ga90 = cells[12].text  # Gol yeme/90
                
                for player in players:
                    if player['oyuncu'] == name:
                        player['kurtaris'] = saves
                        player['kurtaris_yuzde'] = save_pct
                        player['gol_yeme_90'] = ga90
                        break
        
        return players[:100]  # İlk 100 oyuncu
    
    def scrape_whoscored_advanced(self, league_name):
        """WhoScored: Key passes, dribbles, aerial duels"""
        url = f"https://tr.whoscored.com/Regions/252/Tournaments/{league_name}/PlayerStatistics"
        
        driver = webdriver.Chrome(options=self.chrome_options)
        try:
            driver.get(url)
            time.sleep(4)
            
            advanced_stats = []
            rows = driver.find_elements(By.CSS_SELECTOR, '.player-main .table .player-table tbody tr')
            
            for row in rows[:50]:
                cells = row.find_elements(By.TAG_NAME, 'td')
                if len(cells) >= 12:
                    name = cells[2].text.strip()
                    rating = cells[11].text.strip()
                    
                    # Gelişmiş metrikler (pozisyona göre)
                    key_passes = cells[6].text if len(cells) > 6 else '0'
                    dribbles = cells[8].text if len(cells) > 8 else '0'
                    
                    advanced_stats.append({
                        'lig': 'WhoScored',
                        'oyuncu': name,
                        'rating': rating,
                        'key_passes_90': key_passes,
                        'dribbles_90': dribbles,
                        'kaynak': 'WhoScored-Advanced'
                    })
            return advanced_stats
        finally:
            driver.quit()

collector = AdvancedStatsCollector()

@app.route('/api/stats/<league>', methods=['GET'])
def get_league_stats(league):
    """Ana endpoint: /api/stats/superlig, /bundesliga, /premier, /saudi"""
    limit = request.args.get('limit', 50, type=int)
    
    if league not in ['superlig', 'bundesliga', 'premier', 'saudi']:
        return jsonify({'error': 'Geçersiz lig: superlig, bundesliga, premier, saudi'}), 400
    
    cache_key = f"{league}_{limit}"
    if cache_key in collector.cache and time.time() - collector.cache[cache_key]['time'] < 1800:  # 30dk cache
        return jsonify(collector.cache[cache_key]['data'])
    
    print(f"📊 {league.upper()} detaylı istatistikler toplanıyor...")
    stats = collector.get_detailed_stats(league)
    
    if not stats:
        return jsonify({'error': 'Veri alınamadı'}), 503
    
    # DataFrame ile işleme
    df = pd.DataFrame(stats)
    
    # Sayısal sütunları dönüştür
    numeric_cols = ['gol', 'asist', 'xg', 'tackles', 'interceptions', 'kurtaris', 'dakika']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Composite score hesapla
    df['performans_skoru'] = (
        df.get('gol', 0) * 3 +
        df.get('asist', 0) * 2 +
        df.get('xg', 0) * 1.5 +
        df.get('tackles', 0) * 1.2 +
        pd.to_numeric(df.get('pas_yuzde', 0), errors='coerce') * 0.01
    )
    
    # En iyi oyuncular
    top_players = df.nlargest(limit, 'performans_skoru')[['oyuncu', 'pozisyon', 'takim', 
                                                          'gol', 'asist', 'xg', 'pas_yuzde',
                                                          'tackles', 'kurtaris', 'performans_skoru']].to_dict('records')
    
    result = {
        'lig': league.upper(),
        'toplam_oyuncu': len(df),
        'gunluk': datetime.now().strftime('%Y-%m-%d'),
        'oyuncular': top_players
    }
    
    collector.cache[cache_key] = {'data': result, 'time': time.time()}
    return jsonify(result)

@app.route('/api/compare', methods=['GET'])
def compare_leagues():
    """Lig karşılaştırması"""
    leagues = request.args.getlist('ligler[]') or ['superlig', 'bundesliga']
    result = {}
    
    for league in leagues:
        stats = collector.get_detailed_stats(league)
        if stats:
            df = pd.DataFrame(stats)
            result[league] = {
                'ortalama_gol': df['gol'].mean(),
                'ortalama_asist': df['asist'].mean(),
                'en_iyi_oyuncu': df.loc[df['performans_skoru'].idxmax(), 'oyuncu'] if 'performans_skoru' in df else 'N/A'
            }
    
    return jsonify(result)

@app.route('/api/keepers', methods=['GET'])
def get_keepers():
    """Sadece kaleciler"""
    league = request.args.get('lig', 'superlig')
    stats = collector.get_detailed_stats(league)
    df = pd.DataFrame(stats)
    
    keepers = df[df['pozisyon'].str.contains('GK', na=False)][['oyuncu', 'kurtaris', 
                                                               'kurtaris_yuzde', 'gol_yeme_90']].to_dict('records')
    return jsonify({'kaleciler': keepers})

@app.route('/health')
def health_check():
    return jsonify({'status': 'OK', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
