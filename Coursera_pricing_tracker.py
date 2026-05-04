import smtplib
from datetime import date
import os, json
import requests
from email.mime.text import MIMEText

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
GMAIL_DESTINY = os.getenv("GMAIL_DESTINIES")
GMAIL_ERROR_DESTINY = os.getenv("GMAIL_ERROR_DESTINY")
COURSERA_COOKIES = os.getenv("COURSERA_COOKIES")
DATA_FILE = "data.json"

def main():
    api_url = "https://www.coursera.org/api/carts.v2/665807904"
    
    try:
        price = get_price_from_api(api_url)
        
        if price is not None:
            print(f"Precio detectado: {price} MXN")
            save_json(DATA_FILE, price)
            send_email(f"Reporte GHA: ${price} MXN", f"Precio capturado desde API: ${price} MXN", GMAIL_DESTINY)
        else:
            raise ValueError("No se pudo extraer 'totalCartAmount' del JSON de la API.")

    except Exception as e:
        print(f"Error: {e}")
        send_email("ERROR Script GHA", f"Error en la ejecución: {str(e)}", GMAIL_ERROR_DESTINY)

def get_price_from_api(url):
    if not COURSERA_COOKIES:
        raise ValueError("Error: COURSERA_COOKIES no está configurado en los Secrets.")
    
    cookies_list = json.loads(COURSERA_COOKIES)
    cookies_dict = {c['name']: c['value'] for c in cookies_list}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://www.coursera.org/courseraplus"
    }

    response = requests.get(url, headers=headers, cookies=cookies_dict, timeout=15)
    
    if response.status_code == 200:
        data = response.json()
        try:
            elements = data.get("elements", [])
            if elements:
                return elements[0].get("totalCartAmount")
        except (IndexError, KeyError, TypeError):
            return None
    else:
        print(f"Error de API: Status {response.status_code}")
            
    return None

def save_json(filename, price):
    new_entry = {"price": price, "date": str(date.today())}
    
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                content = json.load(f)
                if not isinstance(content, list):
                    history = [content]
                else:
                    history = content
        except json.JSONDecodeError:
            history = []
    else:
        history = []

    history.append(new_entry)

    with open(filename, "w") as f:
        json.dump(history, f, indent=4)

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
