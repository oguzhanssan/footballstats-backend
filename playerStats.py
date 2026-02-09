'''
Önemli Notlar
Selector Güncelleme: Her sitenin HTML'i değişebilir, Chrome DevTools ile selector'ları kontrol edin.
Rate Limiting: time.sleep(2) ekleyin, IP ban önleyin.
EA FC Avantajı: FIFA/FC ratingleri en kapsamlı, 1-99 arası standart skor.
WhoScored: Maç bazlı rating (7.0-9.5 arası), daha gerçekçi performans.
FootyStats: xG, xA gibi gelişmiş metrikler için mükemmel.

Aşağıdaki bağlantılar çalışıyor mu kontrol et, çalışmıyorsa yenilerini bul.
EA FC League ID'leri: 
2026 için kontrol edin (68=SuperLig, 19=Bundesliga, 13=Premier)
'''

import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import warnings
warnings.filterwarnings('ignore')

class FootballDataCollector:
    def __init__(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
    
    def get_ea_fc_ratings(self, league_id):
        """EA FC ratings - Tüm ligler için"""
        league_map = {
            'superlig': '68',      # Süper Lig
            'bundesliga': '19',    # Bundesliga
            'premier': '13',       # Premier League
            'saudi': '1122'        # Saudi Pro League (2025 ID kontrol edin)
        }
        
        url = f'https://www.ea.com/games/ea-sports-fc/ratings/leagues-ratings/{league_id}/{league_map.get(league_id, "68")}'
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            players = []
            for row in soup.select('table tbody tr, .player-row'):
                cols = row.find_all('td')
                if len(cols) >= 4:
                    rating = cols[0].text.strip()
                    name = cols[1].text.strip()
                    players.append({
                        'Lig': league_id.upper(),
                        'Oyuncu': name,
                        'EA_Rating': rating,
                        'Kaynak': 'EA FC 26'
                    })
            return pd.DataFrame(players)
        except:
            return pd.DataFrame()
    
    def get_whoscored_ratings(self, league_code):
        """WhoScored ratings - Lig kodları"""
        whoscored_leagues = {
            'TR': '200/Tournaments/8/Seasons/10042/Stages/22865',  # Süper Lig
            'GB1': 'England-Premier-League',                       # Premier League
            'L1': 'Germany-Bundesliga',                           # Bundesliga
            'SA': 'Saudi-Pro-League'                              # SPL (doğrulayın)
        }
        
        path = whoscored_leagues.get(league_code, 'England-Premier-League')
        url = f'https://tr.whoscored.com/Regions/252/Tournaments/{path}/PlayerStatistics'
        
        driver = webdriver.Chrome(options=self.chrome_options)
        try:
            driver.get(url)
            time.sleep(5)
            
            ratings = []
            rows = driver.find_elements(By.CSS_SELECTOR, '.player-table tbody tr')
            for row in rows[:100]:  # İlk 100 oyuncu
                cells = row.find_elements(By.TAG_NAME, 'td')
                if len(cells) >= 6:
                    name = cells[1].text.strip()
                    rating = cells[-1].text.strip()
                    ratings.append({
                        'Lig': league_code,
                        'Oyuncu': name,
                        'WhoScored_Rating': rating,
                        'Kaynak': 'WhoScored'
                    })
            return pd.DataFrame(ratings)
        finally:
            driver.quit()
    
    def get_footystats_players(self, league_path):
        """FootyStats oyuncu istatistikleri"""
        footystats_leagues = {
            'superlig': 'turkey/super-lig/players',
            'bundesliga': 'germany/bundesliga/players', 
            'premier': 'england/premier-league/players',
            'saudi': 'saudi-arabia/pro-league/players'
        }
        
        url = f'https://footystats.org/{footystats_leagues.get(league_path, "turkey/super-lig/players")}'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            stats = []
            for row in soup.select('table tbody tr'):
                name_elem = row.select_one('.player-name, .name')
                goals_elem = row.select_one('.goals')
                assists_elem = row.select_one('.assists')
                
                if name_elem:
                    stats.append({
                        'Lig': league_path.upper(),
                        'Oyuncu': name_elem.text.strip(),
                        'Gol_90': goals_elem.text.strip() if goals_elem else '0',
                        'Asist_90': assists_elem.text.strip() if assists_elem else '0',
                        'Kaynak': 'FootyStats'
                    })
            return pd.DataFrame(stats[:200])  # Limit 200
        except:
            return pd.DataFrame()
    
    def collect_all_leagues(self):
        """Tüm ligleri topla"""
        leagues = ['superlig', 'bundesliga', 'premier', 'saudi']
        all_data = []
        
        for league in leagues:
            print(f"\n{league.upper()} verileri toplanıyor...")
            
            # EA FC ratings
            ea_df = self.get_ea_fc_ratings(league)
            
            # WhoScored ratings  
            league_code = {'superlig': 'TR', 'bundesliga': 'L1', 'premier': 'GB1', 'saudi': 'SA'}[league]
            who_df = self.get_whoscored_ratings(league_code)
            
            # FootyStats stats
            footy_df = self.get_footystats_players(league)
            
            # Birleştir
            if not ea_df.empty:
                merged = ea_df.merge(footy_df, on=['Lig', 'Oyuncu'], how='outer')
                merged = merged.merge(who_df, on=['Lig', 'Oyuncu'], how='outer')
                all_data.append(merged)
            
            time.sleep(2)  # Rate limit
        
        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            
            # Ortalama rating hesapla
            final_df['Ort_Rating'] = (
                pd.to_numeric(final_df['EA_Rating'], errors='coerce').fillna(80) * 0.4 +
                pd.to_numeric(final_df['WhoScored_Rating'], errors='coerce').fillna(7.0) * 0.6
            )
            
            final_df.to_csv('tum_ligler_oyuncu_yetkinlikleri.csv', index=False, encoding='utf-8')
            print(f"\n✅ {len(final_df)} oyuncu verisi toplandı!")
            print(final_df.groupby('Lig').size())
            print("\nÖrnek veriler:")
            print(final_df[['Lig', 'Oyuncu', 'EA_Rating', 'WhoScored_Rating', 'Ort_Rating', 'Gol_90']].head(10))
            
            return final_df
        return pd.DataFrame()

# Kullanım
if __name__ == "__main__":
    collector = FootballDataCollector()
    result = collector.collect_all_leagues()
    # Tek lig için
    bundesliga_data = collector.get_ea_fc_ratings('bundesliga')
    premier_data = collector.get_whoscored_ratings('GB1')
    # Merge (kulüp bazlı eşleştirme)
    final_analysis = skills_df.merge(kap_df, left_on='Oyuncu', right_on='Bildirim', how='left')
    final_analysis.to_excel('tam_analiz_lig_karsilastirmasi.xlsx')

'''# KAP ile birleştirme (önceki kodunuz)
def full_analysis_with_kap():
    collector = FootballDataCollector()
    skills_df = collector.collect_all_leagues()
    
    # KAP verileri (önceki kodunuz)
    kap_df = scrape_kap_transfers('FENER')
'''


