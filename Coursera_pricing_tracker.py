import smtplib
from datetime import date
import os, json, re
from playwright.sync_api import sync_playwright
from email.mime.text import MIMEText

def main():
    email = os.getenv("GMAIL_USER")
    app_password = os.getenv("GMAIL_PASSWORD")
    destiny = "rodriguezcervantessebastian30@gmail.com"
    
    price = get_price()
    print(f"Precio detectado: {price}")
    
    if price is not None:
        is_price_changed = update_json_and_check_diff(price)
        if is_price_changed:
            print("El precio cambió. Enviando correo...")
            sendEmail(email=email, app_password=app_password, destiny=destiny, price=price)
    else:
        print("No se pudo obtener el precio.")

def get_price():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto("https://www.coursera.org/courseraplus/special/latam-spring-2026-40", wait_until="networkidle")
            page.wait_for_selector(".rc-ReactPriceDisplay", timeout=15000)
            
            spans = page.query_selector_all(".rc-ReactPriceDisplay")
            precios_validos = set()
            with open("debug.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            for span in spans:
                texto = span.inner_text().strip()
                numero = re.sub(r"[^\d]", "", texto)
                if numero:
                    precio = int(numero)
                    if 2000 <= precio <= 5000:
                        precios_validos.add(precio)
            
            return min(precios_validos) if precios_validos else None
        except Exception as e:
            print(f"Error en Playwright: {e}")
            return None
        finally:
            browser.close()

def update_json_and_check_diff(price):
    file_path = os.path.join(os.path.dirname(__file__), "data.json")
    new_entry = {"price": price, "date": str(date.today())}
    dataset = []

    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                dataset = json.load(f)
            except:
                dataset = []

    last_price = dataset[-1]["price"] if dataset else 4590
    dataset.append(new_entry)
    
    with open(file_path, "w") as f:
        json.dump(dataset, f, indent=4)
    
    return price != last_price

def sendEmail(email, app_password, destiny, price):
    if not email or not app_password:
        print("Error: Credenciales de correo no configuradas.")
        return
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 500px; margin: auto; border: 1px solid #eee; padding: 20px;">
            <h2 style="color: #2c3e50;">¡Alerta de Precio!</h2>
            <p>El precio de Coursera Plus es ahora: <b>${price} MXN</b></p>
            <a href="https://www.coursera.org/courseraplus" style="background: #3498db; color: white; padding: 10px; text-decoration: none;">Ver Oferta</a>
        </div>
    </body>
    </html>
    """
    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = "🚀 Coursera Price Alert"
    msg["From"] = email
    msg["To"] = destiny
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email, app_password)
            server.send_message(msg)
            print("Correo enviado exitosamente.")
    except Exception as e:
        print(f"Error enviando correo: {e}")

if __name__ == "__main__":
    main()
