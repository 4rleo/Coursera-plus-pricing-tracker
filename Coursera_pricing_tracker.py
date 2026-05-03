import smtplib
from datetime import date
import os, json
import requests
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
GMAIL_DESTINIES = os.getenv("GMAIL_DESTINIES")
GMAIL_ERROR_DESTINY = os.getenv("GMAIL_ERROR_DESTINY")
COURSERA_COOKIES = os.getenv("COURSERA_COOKIES")
DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")


def main():
    try:
        price = get_price()
        print(f"Precio detectado: {price}")

        if price is None:
            raise ValueError("No se pudo obtener el precio desde la API de Stripe.")

        save_price(price)
        send_price_alert(price)

    except Exception as e:
        print(f"Error en main: {e}")
        send_error_alert(str(e))


def get_price():
    if not COURSERA_COOKIES:
        raise ValueError("La variable COURSERA_COOKIES no está definida.")

    raw_cookies = json.loads(COURSERA_COOKIES)
    cookies_dict = {c["name"]: c["value"] for c in raw_cookies}
    clean_cookies = normalize_cookies(raw_cookies)    
    stripe_url = intercept_stripe_url(clean_cookies)
    print(stripe_url)
    stripe_url = stripe_url.replace("locale=en-US", "locale=es-LA")
    print(stripe_url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-MX,es;q=0.9",
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.coursera.org/courseraplus",
    }

    response = requests.get(stripe_url, headers=headers, cookies=cookies_dict, timeout=15)

    if response.status_code != 200:
        raise ConnectionError(f"Stripe respondió con status {response.status_code}")

    data = response.json()
    payment_intent = data.get("payment_method_preference", {}).get("payment_intent", {})
    amount_cents = payment_intent.get("amount")
    currency = payment_intent.get("currency")

    if not amount_cents or currency != "mxn":
        raise ValueError(f"Precio no encontrado o moneda inesperada: currency={currency}, amount={amount_cents}")

    return amount_cents / 100


def intercept_stripe_url(clean_cookies):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            locale="es-MX",
            timezone_id="America/Mexico_City",
            geolocation={"longitude": -99.1332, "latitude": 19.4326}, 
            permissions=["geolocation"],
            extra_http_headers={
                "Accept-Language": "es-MX,es;q=0.9",
                "X-Forwarded-For": "189.203.0.1" 
            }
        )
        context.add_cookies(clean_cookies)
        page = context.new_page()

        page.goto("https://www.coursera.org/courseraplus")
        text = page.locator(".css-j90x6z").inner_text()
        print(text)
        try:
            page.click("button.css-j90x6z", timeout=10000)
            
        except PlaywrightTimeoutError:
            browser.close()
            raise RuntimeError(
                "No se encontró el botón de checkout. "
                "Posiblemente las cookies caducaron o el layout de Coursera cambió."
            )

        with page.expect_request("**/api.stripe.com/**") as stripe_request:
            pass

        url = stripe_request.value.url
        browser.close()
        return url

def force_locale(url, locale="es-LA"):
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    params["locale"] = [locale]
    new_query = urlencode(params, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


def save_price(price):
    dataset = []

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                dataset = json.load(f)
            except json.JSONDecodeError:
                dataset = []

    dataset.append({"price": price, "date": str(date.today())})

    with open(DATA_FILE, "w") as f:
        json.dump(dataset, f, indent=4)


def normalize_cookies(cookies_list):
    result = []
    for c in cookies_list:
        clean = {
            "name": c["name"],
            "value": c["value"],
            "domain": c.get("domain", ".coursera.org"),
            "path": c.get("path", "/"),
            "secure": c.get("secure", True),
        }

        same_site = str(c.get("sameSite", "Lax")).lower()
        clean["sameSite"] = "None" if same_site in ["no_restriction", "unspecified"] else same_site.capitalize()

        if "expirationDate" in c:
            clean["expires"] = float(c["expirationDate"])

        result.append(clean)
    return result


def send_price_alert(price):
    subject = f"Coursera Plus: ${price} MXN"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 500px; margin: auto; border: 1px solid #eee; padding: 20px; border-radius: 10px;">
            <h2 style="color: #2c3e50;">Reporte diario — Coursera Plus</h2>
            <p style="font-size: 16px;">Precio actual: <b style="color: #27ae60;">${price} MXN</b></p>
            <div style="margin-top: 20px;">
                <a href="https://www.coursera.org/courseraplus"
                   style="background: #2980b9; color: white; padding: 12px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                   Ir a Coursera Plus
                </a>
            </div>
            <p style="color: #7f8c8d; font-size: 12px; margin-top: 30px;">Aviso automático.</p>
        </div>
    </body>
    </html>
    """
    send_email(subject, body, GMAIL_DESTINIES)


def send_error_alert(error_log):
    subject = f"Coursera Tracker — ERROR — {date.today()}"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 500px; margin: auto; border: 1px solid #eee; padding: 20px; border-radius: 10px;">
            <h2 style="color: #c0392b;">Error en el tracker de Coursera Plus</h2>
            <pre style="background: #f5f5f5; padding: 12px; border-radius: 6px; font-size: 13px; overflow-x: auto;">{error_log}</pre>
            <p style="color: #7f8c8d; font-size: 12px; margin-top: 30px;">Aviso automático.</p>
        </div>
    </body>
    </html>
    """
    send_email(subject, body, GMAIL_ERROR_DESTINY)


def send_email(subject, html_body, destiny):
    if not GMAIL_USER or not GMAIL_PASSWORD or not destiny:
        print("Credenciales de correo no configuradas.")
        return

    msg = MIMEText(html_body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = destiny

    recipients = [d.strip() for d in destiny.split(",")]

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.send_message(msg, to_addrs=recipients)
        print(f"Correo enviado: {subject}")
    except Exception as e:
        print(f"Error enviando correo: {e}")


if __name__ == "__main__":
    main()
