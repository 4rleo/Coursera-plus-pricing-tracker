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
        context = browser.new_context(
            locale="es-MX",
            timezone_id="America/Mexico_City",
            geolocation={"latitude": 19.4326, "longitude": -99.1332},
            permissions=["geolocation"]
        )
        
        try:
            cookies_raw = os.getenv("COURSERA_COOKIES")
            if cookies_raw:
                cookies = json.loads(cookies_raw)
                cookies_limpias = []
                
                for cookie in cookies:
                    
                    c = {
                        "name": cookie["name"],
                        "value": cookie["value"],
                        "domain": cookie["domain"],
                        "path": cookie["path"],
                        "secure": cookie["secure"],
                        "httpOnly": cookie["httpOnly"],
                        "sameSite": cookie.get("sameSite", "Lax")
                    }
                    
                    if c["sameSite"] not in ["Strict", "Lax", "None"]:
                        c["sameSite"] = "Lax"
                    
                    cookies_limpias.append(c)
                
                context.add_cookies(cookies_limpias)
            
            page = context.new_page()
            page.goto("https://www.coursera.org/courseraplus", wait_until="networkidle")
            html = page.content()
            with open("debug.html", "w", encoding="utf-8") as f:
                f.write(html)

            
            page.wait_for_selector(".rc-ReactPriceDisplay", timeout=20000)
            
            spans = page.query_selector_all(".rc-ReactPriceDisplay")
            precios_validos = set()
            
            for span in spans:
                texto = span.inner_text().strip()
                
                numero = re.sub(r"[^\d]", "", texto)
                if numero:
                    
                    precio = int(numero)
                    if precio > 10000: # 
                         precio = precio // 100
                         
                    if 2000 <= precio <= 7000:
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

    
    last_price = dataset[-1]["price"] if dataset else 0
    dataset.append(new_entry)
    
    with open(file_path, "w") as f:
        json.dump(dataset, f, indent=4)
    
    
    return price != last_price and last_price != 0

def sendEmail(email, app_password, destiny, price):
    if not email or not app_password:
        print("Error: Credenciales de correo no configuradas.")
        return
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 500px; margin: auto; border: 1px solid #eee; padding: 20px; border-radius: 10px;">
            <h2 style="color: #2c3e50;">¡Oportunidad en Coursera Plus!</h2>
            <p style="font-size: 16px;">El precio actualizado es de: <b style="color: #27ae60;">${price} MXN</b></p>
            <div style="margin-top: 20px;">
                <a href="https://www.coursera.org/courseraplus" 
                   style="background: #2980b9; color: white; padding: 12px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                   Ir a Coursera Plus
                </a>
            </div>
            <p style="color: #7f8c8d; font-size: 12px; margin-top: 30px;">Este es un aviso automático de tu script de monitoreo.</p>
        </div>
    </body>
    </html>
    """
    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = f"🔥 Coursera Plus: ${price} MXN"
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
