#v10 from debugging

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
        # Find the view more button by ID
        qr_buttons = driver.find_elements(By.ID, "view-more")
        if not qr_buttons:
            break
        qr_button = qr_buttons[0]
        
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
for card in cards:
    try:
        title = card.find_element(By.CSS_SELECTOR, "p.card__description").text
        location = card.find_element(By.CSS_SELECTOR, "p.card__address").text
        price = card.find_element(By.CSS_SELECTOR, "p.card__price").text

        image_elem = card.find_elements(By.CSS_SELECTOR, "img.carousel__slide")
        image_url = image_elem[0].get_attribute("src") if image_elem else ""

        link_elem = card.find_element(By.CSS_SELECTOR, "a.card-remax__href")
        url = link_elem.get_attribute("href") if link_elem else ""

        properties.append({
            "titulo": title,
            "ubicacion": location,
            "precio": price,
            "imagen": image_url,
            "url": url
        })
    except Exception as e:
        print(f"⚠️ Error en una tarjeta: {e}")

# Guardar JSON
os.makedirs("docs/data", exist_ok=True)
with open("docs/data/propiedades.json", "w", encoding="utf-8") as f:
    json.dump(properties, f, ensure_ascii=False, indent=2)

driver.quit()
print(f"✅ Scraping completo. {len(properties)} propiedades guardadas en docs/data/propiedades.json")
