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

def build_email_html(price, prev_price=None, prev_date=None):
    if prev_price is not None:
        diff = price - prev_price
        diff_str = f"+${diff:,.2f}" if diff > 0 else f"-${abs(diff):,.2f}"
        diff_color = "#e74c3c" if diff > 0 else "#2ecc71"
        comparison_block = f"""
        <div style="margin-top:20px; padding:15px; background:#1e1e2e; border-radius:8px;">
            <p style="color:#888; margin:0 0 8px 0; font-size:13px;">PRECIO ANTERIOR LOCAL</p>
            <p style="color:#ccc; font-size:22px; margin:0;">${prev_price:,.2f} MXN</p>
            
            <p style="color:{diff_color}; font-size:18px; font-weight:bold; margin:0;">{diff_str} MXN</p>
        </div>
        """
    else:
        comparison_block = """
        <div style="margin-top:20px; padding:15px; background:#1e1e2e; border-radius:8px;">
            <p style="color:#888; margin:0; font-size:13px;">Sin precio anterior registrado.</p>
        </div>
        """

    return f"""
    <html>
    <body style="margin-top:10vh; padding:0; background:#13131f; font-family:'Segoe UI', sans-serif;">
        <div style="max-width:480px; margin:40px auto; background:#1a1a2e; border-radius:16px; overflow:hidden; box-shadow:0 8px 32px rgba(0,0,0,0.4);">
            
            <div style="background:#0070f3; padding:28px 32px;">
                <p style="color:rgba(255,255,255,0.8); margin:0 0 4px 0; font-size:13px; letter-spacing:2px; text-transform:uppercase;">Coursera Plus</p>
                <h1 style="color:white; margin:0; font-size:22px; font-weight:700;">Reporte de Precio</h1>
            </div>

            <div style="padding:28px 32px;">
                <p style="color:#888; margin:0 0 8px 0; font-size:13px; letter-spacing:1px;">PRECIO ACTUAL</p>
                <p style="color:white; font-size:38px; font-weight:800; margin:0;">${price:,.2f} <span style="font-size:18px; color:#aaa;">MXN</span></p>
                <p style="color:#666; font-size:12px; margin:6px 0 0 0;">Detectado el {date.today().strftime('%d %b %Y')}</p>

                {comparison_block}
            </div>

            <div style="padding:16px 32px; background:#13131f;">
                <p style="color:#444; font-size:11px; margin:0; text-align:center;">Generado automáticamente · GitHub Actions</p>
            </div>
        </div>
    </body>
    </html>
    """

def main():
    api_url = "https://www.coursera.org/api/carts.v2/665807904"

    try:
        price = get_price_from_api(api_url)

        if price is not None:
            print(f"Precio detectado: {price} MXN")

            prev_price, prev_date = None, None
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r") as f:
                    history = json.load(f)
                    if isinstance(history, list) and len(history) > 0:
                        last = history[-1]
                        prev_price = last.get("price")
                        prev_date = last.get("date")

            save_json(DATA_FILE, price)
            html = build_email_html(price, prev_price, prev_date)
            send_email(f"Reporte GHA: ${price} MXN", html, GMAIL_DESTINY)
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
    print(f"[send_email] USER={GMAIL_USER!r}, DESTINY={destiny!r}")
    if not GMAIL_USER or not destiny:
        print("[send_email] Abortado: USER o DESTINY está vacío")
        return

    recipients = [d.strip() for d in destiny.split(",")]
    print(f"[send_email] Recipients: {recipients}")

    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = destiny

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.send_message(msg, to_addrs=recipients)
            print("[send_email] Correo enviado OK")
    except Exception as e:
        print(f"[send_email] ERROR: {e}")

if __name__ == "__main__":
    main()
