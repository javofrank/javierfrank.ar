import json
import os
from playwright.sync_api import sync_playwright

OUTPUT_PATH = "web/data/propiedades.json"
TARGET_URL = "https://www.remax.com.ar/agent/javier-frank"


def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # visible browser for local debugging
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        page.goto(TARGET_URL)
        page.wait_for_timeout(2000)

        # Click "Ver más" until it disappears or no new cards load
        while True:
            cards = page.query_selector_all(".card-remax.viewGrid")
            current_count = len(cards)

            view_more = page.query_selector("#view-more")
            if not view_more:
                break

            button = view_more.query_selector("button")
            if not button or not button.is_visible():
                break

            button.scroll_into_view_if_needed()
            page.wait_for_timeout(500)
            button.click()
            page.wait_for_timeout(3000)

            cards = page.query_selector_all(".card-remax.viewGrid")
            if len(cards) == current_count:
                break

        # Extract data
        cards = page.query_selector_all(".card-remax.viewGrid")
        print(f"✅ Se detectaron {len(cards)} propiedades")

        properties = []
        for card in cards:
            try:
                title = card.query_selector("p.card__description").inner_text()
                location = card.query_selector("p.card__address").inner_text()
                price = card.query_selector("p.card__price").inner_text()

                images = card.query_selector_all("img.carousel__slide")
                image_url = images[0].get_attribute("src") if images else ""

                link = card.query_selector("a.card-remax__href")
                url = link.get_attribute("href") if link else ""

                properties.append({
                    "titulo": title,
                    "ubicacion": location,
                    "precio": price,
                    "imagen": image_url,
                    "url": url,
                })
            except Exception as e:
                print(f"⚠️ Error en una tarjeta: {e}")

        # Save JSON
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(properties, f, ensure_ascii=False, indent=2)

        browser.close()

    print(f"✅ Scraping completo. {len(properties)} propiedades guardadas en {OUTPUT_PATH}")


if __name__ == "__main__":
    scrape()
