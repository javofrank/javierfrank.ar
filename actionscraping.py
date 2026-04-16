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

# Usar ChromeDriver preinstalado en GitHub Actions
service = Service(executable_path="/usr/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 15)

# Ir a la página del agente
driver.get("https://www.remax.com.ar/agent/javier-frank")
time.sleep(5)  # Increased wait for full page load

# Scroll to bottom to trigger lazy loading
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(2)

# Clic en "Ver más" hasta que desaparezca o ya no cargue más propiedades
last_count = 0
while True:
    try:
        cards = driver.find_elements(By.CSS_SELECTOR, ".card-remax.viewGrid")  # Updated to original class
        current_count = len(cards)

        # Find button more reliably
        qr_buttons = driver.find_elements(By.XPATH, "//button[contains(text(),'Ver más')]")
        if not qr_buttons:
            qr_buttons = driver.find_elements(By.TAG_NAME, "qr-button")  # Fallback to tag
        if not qr_buttons:
            break
        qr_button = qr_buttons[0]

        if not qr_button.is_displayed():
            break

        driver.execute_script("arguments[0].scrollIntoView(true);", qr_button)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", qr_button)
        time.sleep(3)

        cards = driver.find_elements(By.CSS_SELECTOR, ".card-remax.viewGrid")
        if len(cards) == current_count:
            break
    except Exception as e:
        print("⚠️ No se puede hacer clic en 'Ver más':", e)
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
