# Önceki koddaki Transfermarkt'ı FootyStats + Apify ile değiştirin. 
# Apify API key alın (apify.com), FootyStats için docs'a bakın. Haber scraping'i yedekleyin.
# Bu kod FootyStats'tan anlık değerler çeker (2026 verileri mevcut), 
# Apify ile Transfermarkt'ı bypass eder. Selector'ları tarayıcı 
# inspect ile doğrulayın (değişebilir). 
# Haberler için regex ekleyin: 
# import re; values = re.findall(r'€(\d+(?:\.\d+)?m?)', text).
#

import requests
import pandas as pd
from bs4 import BeautifulSoup
import time

# Apify Transfermarkt Scraper (alternatif)
APIFY_TOKEN = 'YOUR_APIFY_TOKEN'
APIFY_ACTOR = 'data_xplorer/transfermarkt-api-scraper'  # Süper Lig için input ayarlayın

def get_transfermarkt_via_apify(lig='TR1', sezon='2025'):
    url = f'https://api.apify.com/v2/acts/{APIFY_ACTOR}/runs'
    payload = {
        'token': APIFY_TOKEN,
        'input': {'search': f'Süper Lig {sezon}', 'maxItems': 100}  # Piyasa değerleri için
    }
    response = requests.post(url, json=payload)
    run_id = response.json()['data']['id']
    
    # Sonuç bekle (sync için wait)
    time.sleep(30)
    result_url = f'https://api.apify.com/v2/acts/{APIFY_ACTOR}/runs/{run_id}/dataset/items?token={APIFY_TOKEN}&format=json'
    data = requests.get(result_url).json()
    df = pd.DataFrame(data)
    df.to_csv('transfermarkt_superlig.csv', index=False)
    return df[['name', 'marketValue', 'club', 'transferFee']]  # Kolonlar approx

def scrape_footystats_market_values():
    url = 'https://footystats.org/turkey/super-lig/market-values'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    players = []
    for row in soup.select('table tbody tr'):  # Tablo selector'ını inspect ile doğrulayın
        cols = row.find_all('td')
        if len(cols) > 3:
            name = cols[1].text.strip()
            value = cols[2].text.strip()
            players.append({'Oyuncu': name, 'Değer': value})
    
    df = pd.DataFrame(players)
    df.to_csv('footystats_piyasa.csv', index=False)
    return df

def scrape_guncel_degerler_haber(url):
    # Örn: https://www.gazeteilksayfa.com/transfermarkt-super-lig-guncellemesi...
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Snippet bazlı extract (manuel uyarlayın)
    text = soup.get_text()
    # Regex ile değerler çekin, örn: '€\d+' 
    df = pd.DataFrame({'Kaynak': 'Haber', 'Veri': text[:500]})  # Basit
    return df

def main():
    print("FootyStats piyasa değerleri alınıyor...")
    footy_df = scrape_footystats_market_values()
    print(footy_df.head())
    
    print("Apify ile Transfermarkt...")
    apify_df = get_transfermarkt_via_apify()
    print(apify_df.head() if not apify_df.empty else "API hatası")
    
    # Haber yedeği
    haber_df = scrape_guncel_degerler_haber('https://www.gazeteilksayfa.com/transfermarkt-super-lig-guncellemesi-en-pahali-futbolcular-aciklandi-288456h.htm')
    haber_df.to_csv('haber_piyasa.csv')

if __name__ == "__main__":
    main()
