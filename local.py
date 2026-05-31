import smtplib
from datetime import date
import os, json
import requests
import re
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

GMAIL_USER = "cpricingtracker@gmail.com"
GMAIL_PASSWORD = "vgqfsrquhzyobqty"
GMAIL_ERROR_DESTINY = "rodriguezcervantessebastian30@gmail.com"
GMAIL_DESTINIES = "rodriguezcervantessebastian30@gmail.com, rodriguezcervant3sseb4stian@gmail.com"
COURSERA_COOKIES = "cookie.json"
DATA_FILE = os.path.join(os.path.dirname(__file__), "data_local.json")

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
    if not os.path.exists(COURSERA_COOKIES):
        raise FileNotFoundError(f"No se encontró el archivo: {COURSERA_COOKIES}")

    with open(COURSERA_COOKIES, "r") as f:
        raw_cookies = json.load(f)

    cookies_dict = {c["name"]: c["value"] for c in raw_cookies}
    clean_cookies = normalize_cookies(raw_cookies)    
    stripe_url = intercept_stripe_url(clean_cookies)
    
    stripe_url = stripe_url.replace("locale=en-US", "locale=es-LA")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-MX,es;q=0.9",
        "Content-Type": "application/json",
        "Referer": "https://www.coursera.org/courseraplus",
    }

    response = requests.get(stripe_url, headers=headers, cookies=cookies_dict, timeout=15)

    if response.status_code != 200:
        raise ConnectionError(f"Stripe responded with status {response.status_code}")

    data = response.json()
    pi = data.get("payment_method_preference", {}).get("payment_intent", {})
    amount_cents = pi.get("amount")
    
    if not amount_cents:
        raise ValueError("No se encontró el monto en la respuesta de Stripe.")

    return amount_cents / 100

def intercept_stripe_url(clean_cookies):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(locale="es-MX")
        context.add_cookies(clean_cookies)
        page = context.new_page()

        page.goto("https://www.coursera.org/courseraplus")
        
        try:
            page.wait_for_selector("button.css-j90x6z", timeout=15000)
            with page.expect_request("**/api.stripe.com/**") as stripe_request:
                page.click("button.css-j90x6z")
            
            url = stripe_request.value.url
            browser.close()
            return url
        except PlaywrightTimeoutError:
            browser.close()
            raise RuntimeError("Timeout: No se detectó la petición a Stripe.")

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

def save_price(price):
    dataset = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                dataset = json.load(f)
            except:
                dataset = []
    dataset.append({"price": price, "date": str(date.today())})
    with open(DATA_FILE, "w") as f:
        json.dump(dataset, f, indent=4)

def send_price_alert(price):
    subject = f"Coursera Plus: ${price} MXN"
    body = f"<html><body><h2>Precio actual detectado localmente: ${price} MXN</h2></body></html>"
    send_email(subject, body, GMAIL_DESTINIES)

def send_error_alert(error_log):
    subject = f"Coursera Tracker — ERROR"
    body = f"<html><body><pre>{error_log}</pre></body></html>"
    send_email(subject, body, GMAIL_ERROR_DESTINY)

def send_email(subject, html_body, destiny):
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
    except Exception as e:
        print(f"Error mail: {e}")

if __name__ == "__main__":
    main()
