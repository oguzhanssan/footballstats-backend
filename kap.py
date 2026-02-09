# Aşağıdaki kod KAP scraping, Companies House API ve Capology entegrasyonu 
# yapar. Verileri CSV'ye birleştirir. KAP için Selenium kullanın 
# (PDF'ler için), diğerleri requests ile.
''' """
Genişletme
KAP Arama İyileştirme: PDF bildirimleri PyMuPDF ile parse edin (pip install pymupdf).

Yurt Dışı API: Companies House API key alın, UEFA raporları indirin.

Birleştirme: Tüm CSV'leri pd.read_csv ile merge edip dashboard yapın (Streamlit).
Resmi veriler piyasa değerinden daha güvenilir (bonservis gerçek rakamlar). Başka lig ekleyin!
"""
'''
import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import re
from io import StringIO

# KAP arama URL
KAP_SEARCH = 'https://www.kap.org.tr/tr/sirket-bilgileri/ozet/{ticker}-Istanbul'}  # Ticker: FENER (FB), GALAS (GS), BEsim (BJK)

def scrape_kap_transfers(kulup_ticker):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    
    driver.get(f'https://www.kap.org.tr/tr/BildirimSorgu?ara={kulup_ticker}+transfer')
    time.sleep(5)
    
    transfers = []
    for row in driver.find_elements(By.CSS_SELECTOR, 'table tr'):
        text = row.text
        if 'bonservis' in text.lower() or 'transfer bedeli' in text.lower():
            fee_match = re.search(r'(\d+(?:\.\d+)?[€$€]|undisclosed)', text)
            transfers.append({'Kulüp': kulup_ticker, 'Bildirim': text[:200], 'Tahmini Bedel': fee_match.group(1) if fee_match else 'N/A'})
    
    driver.quit()
    return pd.DataFrame(transfers)

def get_companies_house_finans(pl_club):  # Premier League, örn 'Arsenal FC'
    # Gerçek API: https://developer.company-information.service.gov.uk/
    # Demo: Mock veya scraping Kinnaird
    url = f'https://kinnairdsports.com/premier-league/{pl_club.lower().replace(" ", "-")}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Finansal tablo extract (inspect ile uyarlayın)
    finans = {'Kulüp': pl_club, 'Revenue': 'Data scraped', 'Wages': 'Data scraped'}
    return pd.DataFrame([finans])

def get_capology_spl():
    url = 'https://www.capology.com/sa/saudi-pro-league/finances/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    clubs = []
    for club_row in soup.select('.club-row'):  # Selector uyarla
        name = club_row.select_one('.club-name').text
        revenue = club_row.select_one('.revenue').text
        clubs.append({'Kulüp': name, 'Revenue': revenue, 'P&L': 'Extracted'})
    return pd.DataFrame(clubs)

def get_openligadb_bundesliga():
    url = 'https://api.openligadb.de/getmatchdata/BL1/2025'  # 2025/26 sezonu
    data = requests.get(url).json()
    df = pd.json_normalize(data)
    df.to_csv('bundesliga_maclar.csv')
    return df[['Team1.TeamName', 'Team2.TeamName', 'MatchDateTime']]

def main():
    # TR KAP
    kap_fb = scrape_kap_transfers('FENER')
    kap_gs = scrape_kap_transfers('GALAS')
    kap_df = pd.concat([kap_fb, kap_gs], ignore_index=True)
    kap_df.to_csv('kap_transfers.csv', index=False)
    
    # Premier League
    pl_df = get_companies_house_finans('Arsenal FC')
    pl_df.to_csv('premier_finans.csv')
    
    # SPL
    spl_df = get_capology_spl()
    spl_df.to_csv('spl_finans.csv')
    
    # Bundesliga
    bl_df = get_openligadb_bundesliga()
    
    print("KAP Transfers:", kap_df.head())
    print("Veriler CSV'lere kaydedildi!")

if __name__ == "__main__":
    main()
