#v12 playwright

import json
import os
import time

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

AGENT_URL = "https://www.remax.com.ar/agent/javier-frank"
OUTPUT_PATH = "docs/data/propiedades.json"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
BROWSER_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
    "--disable-extensions",
]
LISTING_LINKS = "a[href*='/listings/']"
NON_PROPERTY_SLUGS = {"buy", "sell", "rent", "office", "agent"}
METRIC_TOKENS = ["m²", "ambientes", "baños", "bano", "cubiertos", "totales", "terreno", "sup."]

# Texto visible de los <p> de una card. innerText de un elemento con display:none
# devuelve su textContent (ej. "Corredores responsables", solo para mobile),
# así que se filtran los no renderizados.
VISIBLE_P_TEXTS_JS = """root => [...root.querySelectorAll('p')]
    .filter(el => el.checkVisibility())
    .map(el => el.innerText.trim())
    .filter(Boolean)"""
HREFS_JS = "els => els.map(a => a.href)"


def is_metric_text(text):
    text_l = text.lower()
    return any(token in text_l for token in METRIC_TOKENS)


def is_price_text(text):
    text_l = text.lower()
    return "usd" in text_l or "ars" in text_l or "expensas" in text_l


def normalize_listing_url(url):
    if not url:
        return ""
    return url.split("?")[0].rstrip("/")


def is_property_listing_url(url):
    slug = url.split("/listings/", 1)[1].strip("/")
    return bool(slug) and slug.lower() not in NON_PROPERTY_SLUGS


def pick_property_image(page, url):
    slug = url.split("/listings/", 1)[1]
    for img in page.locator(f"a[href*='/listings/{slug}'] img").all():
        src = (img.get_attribute("src") or "").strip()
        src_l = src.lower()
        # Evitar iconos de métricas embebidos en la card.
        if src and "/assets/icons/" not in src_l and not src_l.endswith(".svg"):
            return src
    return ""


def listing_count(page):
    hrefs = page.eval_on_selector_all(LISTING_LINKS, HREFS_JS)
    return len({normalize_listing_url(h) for h in hrefs if h})


def wait_for_listing(page, timeout_s=30, poll_s=1.5):
    """Espera el listado; si no aparece, scrollea un poco para disparar la carga."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if page.locator("#cards-props").count() or listing_count(page):
            return True
        page.evaluate("window.scrollBy(0, 700);")
        time.sleep(poll_s)
    return False


def click_view_more_until_done(page):
    while True:
        button = page.locator("#view-more button")
        if not button.count() or not button.first.is_visible():
            return
        before = listing_count(page)
        button.first.scroll_into_view_if_needed()
        time.sleep(0.5)
        button.first.evaluate("el => el.click()")
        time.sleep(3)
        if listing_count(page) == before:
            return


def launch_browser(playwright):
    """Usa el Google Chrome instalado; si no está, cae al Chromium que trae Playwright."""
    try:
        return playwright.chromium.launch(channel="chrome", headless=True, args=BROWSER_ARGS)
    except PlaywrightError as e:
        print(f"ℹ️ No se pudo usar Google Chrome ({str(e).splitlines()[0]}); usando Chromium de Playwright.")
        return playwright.chromium.launch(headless=True, args=BROWSER_ARGS)


def dump_diagnostics(page):
    page.screenshot(path="scrape_error.png", full_page=True)
    with open("scrape_error.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    body_text = page.evaluate("document.body ? document.body.innerText : ''") or ""
    print(f"ℹ️ URL actual: {page.url}")
    print(f"ℹ️ Título: {page.title()}")
    print(f"ℹ️ Texto de la página (primeros 1000 chars):\n{body_text[:1000]}")


def parse_anchor(page, anchor):
    """Devuelve la propiedad de un anchor de listing, o None si no es una card útil."""
    # .href devuelve la URL absoluta.
    url = normalize_listing_url(anchor.evaluate("a => a.href"))
    if not url or not is_property_listing_url(url):
        return None

    p_texts = anchor.evaluate(VISIBLE_P_TEXTS_JS)
    price_parts = [t for t in p_texts if is_price_text(t)]
    content_texts = [t for t in p_texts if not is_price_text(t) and not is_metric_text(t)]
    location = next((t for t in content_texts if any(c.isdigit() for c in t)), "")
    title = next((t for t in reversed(content_texts) if t != location), "")
    if not title and p_texts:
        title = p_texts[-1]

    return {
        "text_score": sum(len(t) for t in p_texts),
        "titulo": title,
        "ubicacion": location,
        "precio": " | ".join(price_parts[:2]),
        "imagen": pick_property_image(page, url),
        "url": url,
    }


def extract_properties(page):
    anchors = page.locator(LISTING_LINKS).all()
    print(f"ℹ️ Links de listings detectados: {len(anchors)}")

    # Cada propiedad aparece en varios anchors (imagen, card...): quedarse con el de más texto.
    by_url = {}
    for anchor in anchors:
        try:
            item = parse_anchor(page, anchor)
        except PlaywrightError as e:
            print(f"⚠️ Error procesando anchor listing: {e}")
            continue
        if item is None:
            continue
        current = by_url.get(item["url"])
        if current is None or item["text_score"] > current["text_score"]:
            by_url[item["url"]] = item

    return [
        {k: v for k, v in item.items() if k != "text_score"}
        for item in by_url.values()
        if item["titulo"] or item["ubicacion"] or item["precio"]
    ]


def scrape():
    with sync_playwright() as p:
        browser = launch_browser(p)
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1920, "height": 1080},
            locale="es-AR",
        )
        # Bloquear imágenes para acelerar la carga.
        context.route(
            "**/*",
            lambda route: route.abort() if route.request.resource_type == "image" else route.continue_(),
        )
        page = context.new_page()
        page.set_default_timeout(30_000)
        page.goto(AGENT_URL, wait_until="load")

        # Hasta ~60s en total, recargando una vez si no aparece el listado.
        loaded = False
        for attempt in range(2):
            if wait_for_listing(page):
                loaded = True
                break
            print(f"⚠️ Listado no detectado (intento {attempt + 1}), recargando...")
            page.reload(wait_until="load")

        if not loaded:
            dump_diagnostics(page)
            browser.close()
            raise RuntimeError(
                "No se pudo detectar el listado de propiedades tras reintentos. "
                "DOM posiblemente cambiado o acceso bloqueado."
            )

        # Scroll para disparar la carga diferida
        for _ in range(3):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        click_view_more_until_done(page)
        properties = extract_properties(page)
        browser.close()

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(properties, f, ensure_ascii=False, indent=2)
    print(f"✅ Scraping completo. {len(properties)} propiedades guardadas en {OUTPUT_PATH}")


if __name__ == "__main__":
    scrape()
