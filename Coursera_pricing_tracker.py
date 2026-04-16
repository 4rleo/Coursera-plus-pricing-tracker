import smtplib
from datetime import date
import os, json, re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from email.mime.text import MIMEText
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def main():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # En GitHub Actions no solemos necesitar binary_location si usamos chromium-browser del sistema
    
    # --- SEGURIDAD: Usar variables de entorno ---
    email = os.getenv("GMAIL_USER")
    app_password = os.getenv("GMAIL_PASSWORD")
    destiny = "rodriguezcervantessebastian30@gmail.com"
    
    price = get_price(options=options)
    print(f"Precio detectado: {price}")
    
    if price is not None: 
        is_price_changed = update_json_and_check_diff(price)
        if is_price_changed:
            print("El precio cambió. Enviando correo...")
            sendEmail(email=email, app_password=app_password, destiny=destiny, price=price)
    else:
        print("No se pudo obtener el precio.")

def get_price(options):
    driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://www.coursera.org/courseraplus/special/latam-spring-2026-40")
        # Espera hasta 10 segundos a que aparezca el elemento del precio
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "rc-ReactPriceDisplay")))
        
        price_spans = driver.find_elements(By.CLASS_NAME, "rc-ReactPriceDisplay")
        precios_validos = set()

        for span in price_spans:
            texto = span.text.strip()
            numero = re.sub(r"[^\d]", "", texto)
            if numero:
                precio = int(numero)
                if 2000 <= precio <= 5000:
                    precios_validos.add(precio)

        return min(precios_validos) if precios_validos else None
    except Exception as e:
        print(f"Error en Selenium: {e}")
        return None
    finally:
        driver.quit()

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