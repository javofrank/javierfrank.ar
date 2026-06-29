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
from selenium.common.exceptions import TimeoutException

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

# Usar ChromeDriver preinstalado cuando existe en GitHub Actions.
# Fallback a Selenium Manager para mayor robustez.
chromedriver_path = "/usr/bin/chromedriver"
if os.path.exists(chromedriver_path):
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)
else:
    driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 30)


def first_text(element, selectors):
    for selector in selectors:
        nodes = element.find_elements(By.CSS_SELECTOR, selector)
        for node in nodes:
            text = (node.text or "").strip()
            if text:
                return text
    return ""


def is_metric_text(text):
    text_l = text.lower()
    metric_tokens = ["m²", "ambientes", "baños", "bano", "cubiertos", "totales", "terreno", "sup."]
    return any(token in text_l for token in metric_tokens)


def is_price_text(text):
    text_l = text.lower()
    return "usd" in text_l or "ars" in text_l or "expensas" in text_l


def normalize_listing_url(url):
    if not url:
        return ""
    return url.split("?")[0].rstrip("/")


def is_property_listing_url(url):
    if "/listings/" not in url:
        return False
    slug = url.split("/listings/", 1)[1].strip("/")
    if not slug:
        return False
    non_property_slugs = {"buy", "sell", "rent", "office", "agent"}
    return slug.lower() not in non_property_slugs


def pick_property_image(driver, url):
    if not url:
        return ""

    slug = url.split("/listings/", 1)[1]
    candidate_images = driver.find_elements(By.CSS_SELECTOR, f"a[href*='/listings/{slug}'] img")
    for img in candidate_images:
        src = (img.get_attribute("src") or "").strip()
        if not src:
            continue
        src_l = src.lower()
        # Evitar iconos de métricas embebidos en la card.
        if "/assets/icons/" in src_l or src_l.endswith(".svg"):
            continue
        return src

    return ""

# Ir a la página del agente
driver.get("https://www.remax.com.ar/agent/javier-frank")
time.sleep(10)

# Esperar contenedor/listado usando selectores legacy + nuevos.
try:
    wait.until(lambda d: (
        len(d.find_elements(By.CSS_SELECTOR, ".card-remax.viewGrid")) > 0
        or len(d.find_elements(By.CSS_SELECTOR, "#cards-props")) > 0
        or len(d.find_elements(By.CSS_SELECTOR, "a[href*='/listings/']")) > 0
    ))
except TimeoutException:
    driver.save_screenshot("scrape_error.png")
    raise RuntimeError("No se pudo detectar el listado de propiedades. DOM posiblemente cambiado.")

# Scroll to trigger loading
for _ in range(3):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

# Clic en "Ver más" hasta que desaparezca
while True:
    old_cards = driver.find_elements(By.CSS_SELECTOR, ".card-remax.viewGrid")
    listing_links = {
        normalize_listing_url(link.get_attribute("href"))
        for link in driver.find_elements(By.CSS_SELECTOR, "a[href*='/listings/']")
        if link.get_attribute("href")
    }
    current_count = max(len(old_cards), len(listing_links))
    
    try:
        # Buscar botón de "Ver más" en ambos DOMs.
        real_button = None

        qr_buttons = driver.find_elements(By.ID, "view-more")
        if qr_buttons:
            nested_buttons = qr_buttons[0].find_elements(By.TAG_NAME, "button")
            if nested_buttons:
                real_button = nested_buttons[0]

        if real_button is None:
            text_buttons = driver.find_elements(By.XPATH, "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚ', 'abcdefghijklmnopqrstuvwxyzáéíóú'), 'ver más')]")
            if text_buttons:
                real_button = text_buttons[0]

        if real_button is None:
            break
        
        if not real_button.is_displayed():
            break
        
        driver.execute_script("arguments[0].scrollIntoView(true);", real_button)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", real_button)
        time.sleep(3)
        
        old_cards_after = driver.find_elements(By.CSS_SELECTOR, ".card-remax.viewGrid")
        listing_links_after = {
            normalize_listing_url(link.get_attribute("href"))
            for link in driver.find_elements(By.CSS_SELECTOR, "a[href*='/listings/']")
            if link.get_attribute("href")
        }
        after_count = max(len(old_cards_after), len(listing_links_after))
        if after_count == current_count:
            break
    except Exception as e:
        print(f"⚠️ No more 'Ver más' button or error: {e}")
        break

# Extraer info del DOM
cards = driver.find_elements(By.CSS_SELECTOR, ".card-remax.viewGrid")
listing_anchors = driver.find_elements(By.CSS_SELECTOR, "a[href*='/listings/']")
print(f"ℹ️ Legacy cards detectadas: {len(cards)}")
print(f"ℹ️ Links de listings detectados: {len(listing_anchors)}")

properties = []

if cards:
    # Parser legacy (DOM anterior).
    for card in cards:
        try:
            title = first_text(card, ["p.card__description"])
            location = first_text(card, ["p.card__address"])
            price = first_text(card, ["p.card__price"])

            image_elem = card.find_elements(By.CSS_SELECTOR, "img.carousel__slide")
            image_url = image_elem[0].get_attribute("src") if image_elem else ""

            link_elem = card.find_elements(By.CSS_SELECTOR, "a.card-remax__href")
            url = link_elem[0].get_attribute("href") if link_elem else ""

            if url:
                properties.append({
                    "titulo": title,
                    "ubicacion": location,
                    "precio": price,
                    "imagen": image_url,
                    "url": normalize_listing_url(url)
                })
        except Exception as e:
            print(f"⚠️ Error en una tarjeta legacy: {e}")
else:
    # Parser nuevo (DOM actual por anchors de listing).
    by_url = {}
    for anchor in listing_anchors:
        try:
            url = normalize_listing_url(anchor.get_attribute("href"))
            if not url or not is_property_listing_url(url):
                continue

            candidate = by_url.get(url, {"text_score": -1})

            p_texts = [
                (node.text or "").strip()
                for node in anchor.find_elements(By.CSS_SELECTOR, "p")
                if (node.text or "").strip()
            ]
            text_score = sum(len(text) for text in p_texts)
            if text_score <= candidate.get("text_score", -1):
                continue

            price_parts = [text for text in p_texts if is_price_text(text)]
            price = " | ".join(price_parts[:2]) if price_parts else ""

            content_texts = [text for text in p_texts if not is_price_text(text) and not is_metric_text(text)]
            location = next((text for text in content_texts if any(char.isdigit() for char in text)), "")
            title = ""
            for text in reversed(content_texts):
                if text != location:
                    title = text
                    break
            if not title and p_texts:
                title = p_texts[-1]

            image_url = pick_property_image(driver, url)

            by_url[url] = {
                "text_score": text_score,
                "titulo": title,
                "ubicacion": location,
                "precio": price,
                "imagen": image_url,
                "url": url
            }
        except Exception as e:
            print(f"⚠️ Error procesando anchor listing: {e}")

    properties = [
        {k: v for k, v in item.items() if k != "text_score"}
        for item in by_url.values()
        if item.get("titulo") or item.get("ubicacion") or item.get("precio")
    ]

print(f"✅ Se detectaron {len(properties)} propiedades parseadas")

# Guardar JSON
os.makedirs("docs/data", exist_ok=True)
with open("docs/data/propiedades.json", "w", encoding="utf-8") as f:
    json.dump(properties, f, ensure_ascii=False, indent=2)

driver.quit()
print(f"✅ Scraping completo. {len(properties)} propiedades guardadas en docs/data/propiedades.json")
