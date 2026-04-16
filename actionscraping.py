#v7 from GC debugging

import json
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

# Configurar Chrome en modo headless para GitHub Actions
options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--disable-extensions')
options.add_argument('--disable-plugins')
options.add_argument('--disable-images')  # Speed up loading
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
options.add_argument('--window-size=1920,1080')

# Usar ChromeDriver preinstalado en GitHub Actions
service = Service(executable_path="/usr/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 30)

# Ir a la página del agente
driver.get("https://www.remax.com.ar/agent/javier-frank")
time.sleep(10)

# Wait for the cards container
wait.until(EC.presence_of_element_located((By.ID, "cards-props")))

# Scroll to trigger loading
for _ in range(3):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

# Clic en "Ver más" hasta que desaparezca
last_count = 0
while True:
    cards = driver.find_elements(By.CSS_SELECTOR, ".card-remax.viewGrid")
    current_count = len(cards)
    
    try:
        # Wait for the view more container
        wait.until(EC.presence_of_element_located((By.ID, "properties-view-more")))
        view_more_div = driver.find_element(By.ID, "properties-view-more")
        
        # Find qr-button inside
        qr_button = view_more_div.find_element(By.TAG_NAME, "qr-button")
        
        # Find the button inside qr-button
        real_button = qr_button.find_element(By.TAG_NAME, "button")
        
        if not real_button.is_displayed():
            break
        
        driver.execute_script("arguments[0].scrollIntoView(true);", real_button)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", real_button)
        time.sleep(3)
        
        cards = driver.find_elements(By.CSS_SELECTOR, ".card-remax.viewGrid")
        if len(cards) == current_count:
            break
    except Exception as e:
        print(f"⚠️ No more 'Ver más' button or error: {e}")
        break

# Extraer info del DOM
cards = driver.find_elements(By.CSS_SELECTOR, ".card-remax.viewGrid")
print(f"✅ Se detectaron {len(cards)} propiedades")

properties = []
for card
