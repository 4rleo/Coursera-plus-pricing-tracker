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
        diff_color = "#dc2626" if diff > 0 else "#16a34a"
        diff_bg = "#fef2f2" if diff > 0 else "#f0fdf4"
        diff_border = "#fecaca" if diff > 0 else "#bbf7d0"
        arrow = "↑" if diff > 0 else ("↓" if diff < 0 else "→")
        comparison_block = f"""
        <tr>
            <td style="padding:0 32px 28px 32px;">
                <table width="100%" cellpadding="0" cellspacing="0" style="background:{diff_bg}; border:1px solid {diff_border}; border-radius:12px;">
                    <tr>
                        <td style="padding:18px 20px;">
                            <p style="color:#6b7280; margin:0 0 10px 0; font-size:11px; font-weight:600; letter-spacing:1.5px; text-transform:uppercase;">Comparación con precio local</p>
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td>
                                        <p style="color:#374151; font-size:13px; margin:0 0 2px 0;">Precio anterior</p>
                                        <p style="color:#111827; font-size:20px; font-weight:700; margin:0;">${prev_price:,.2f} <span style="font-size:13px; color:#6b7280; font-weight:400;">MXN</span></p>
                                        
                                    </td>
                                    <td style="text-align:right; vertical-align:middle;">
                                        <p style="color:{diff_color}; font-size:26px; font-weight:800; margin:0;">{arrow} {diff_str}</p>
                                        <p style="color:{diff_color}; font-size:11px; margin:2px 0 0 0; opacity:0.8;">MXN</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        """
    else:
        comparison_block = f"""
        <tr>
            <td style="padding:0 32px 28px 32px;">
                <table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb; border:1px solid #e5e7eb; border-radius:12px;">
                    <tr>
                        <td style="padding:16px 20px;">
                            <p style="color:#9ca3af; margin:0; font-size:13px;">Sin precio local registrado para comparar.</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background:#f3f4f6; font-family:'Segoe UI', Arial, sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6; padding:40px 16px;">
            <tr>
                <td align="center">
                    <table width="100%" cellpadding="0" cellspacing="0" style="max-width:480px; background:#ffffff; border-radius:16px; overflow:hidden; box-shadow:0 4px 24px rgba(0,0,0,0.08);">
                        
                        <tr>
                            <td style="background:#2563eb; padding:28px 32px;">
                                <p style="color:rgba(255,255,255,0.7); margin:0 0 4px 0; font-size:11px; font-weight:600; letter-spacing:2px; text-transform:uppercase;">Coursera Plus · Monitor</p>
                                <h1 style="color:#ffffff; margin:0; font-size:22px; font-weight:700;">Reporte de Precio</h1>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding:28px 32px 20px 32px;">
                                <p style="color:#6b7280; margin:0 0 6px 0; font-size:11px; font-weight:600; letter-spacing:1.5px; text-transform:uppercase;">Precio actual</p>
                                <p style="color:#111827; font-size:42px; font-weight:800; margin:0; line-height:1;">${price:,.2f} <span style="font-size:18px; color:#9ca3af; font-weight:400;">MXN</span></p>
                                <p style="color:#9ca3af; font-size:12px; margin:8px 0 0 0;">Detectado el {date.today().strftime('%d de %B de %Y')}</p>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding:0 32px 24px 32px;">
                                <hr style="border:none; border-top:1px solid #e5e7eb; margin:0 0 24px 0;">
                            </td>
                        </tr>

                        {comparison_block}

                        <tr>
                            <td style="background:#f9fafb; padding:14px 32px; border-top:1px solid #e5e7eb;">
                                <p style="color:#9ca3af; font-size:11px; margin:0; text-align:center;">Generado automáticamente · GitHub Actions</p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
def main():
    API_FILE = open("API_URL.txt", 'r')
    api_url = API_FILE.read()
    API_FILE.close()
    
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
