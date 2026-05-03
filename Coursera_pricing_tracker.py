import smtplib
from datetime import date
import os, json, re
import requests
from email.mime.text import MIMEText


GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
GMAIL_DESTINY = os.getenv("GMAIL_DESTINY")
GMAIL_ERROR_DESTINY = os.getenv("GMAIL_ERROR_DESTINY")
COURSERA_COOKIES = os.getenv("COURSERA_COOKIES")
DATA_FILE = "data.json"

def main():
    
    carrito_url = "https://www.coursera.org/payments/checkout?cartId=665804560"
    
    try:
        
        price = get_price_static(carrito_url)
        print(f"Precio detectado en GHA: {price}")
        
        if price is not None:
            save_json(DATA_FILE, price)
            send_email(f"Reporte Diario GHA: ${price} MXN", f"Precio capturado: ${price}", GMAIL_DESTINY)
        else:
            raise ValueError("No se pudo obtener el precio desde el carrito en la nube.")

    except Exception as e:
        print(f"Error en GHA: {e}")
        send_email("ERROR Script GHA", str(e), GMAIL_ERROR_DESTINY)

def get_price_static(url):
    if not COURSERA_COOKIES: return None
    
    cookies_list = json.loads(COURSERA_COOKIES)
    cookies_dict = {c['name']: c['value'] for c in cookies_list}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-MX,es;q=0.9",
        "Referer": "https://www.coursera.org/courseraplus"
    }

    
    response = requests.get(url, headers=headers, cookies=cookies_dict, timeout=15)
    
    if response.status_code == 200:
        
        match = re.search(r'"amount":(\d+),"currency":"mxn"', response.text.lower())
        if match:
            return int(match.group(1)) / 100
            
    return None

def save_json(filename, price):
    entry = {"price": price, "date": str(date.today())}
    with open(filename, "w") as f:
        json.dump(entry, f, indent=4)

def send_email(subject, body, destiny):
    if not GMAIL_USER or not destiny: return
    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = destiny
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.send_message(msg)

if __name__ == "__main__":
    main()
