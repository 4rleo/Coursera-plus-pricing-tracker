import smtplib
from datetime import date
import os, json, re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from email.mime.text import MIMEText
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC




def main():
    options = Options()
    price = 0
    email = "cpricingtracker@gmail.com"
    app_password = " qufe lprd acsw ddrb "
    destiny = "rodriguezcervantessebastian30@gmail.com"
    options.add_argument("--headless")
    price = get_price(options=options)
    print(price)
    is_price_changed= False
    if price is not None: 
        is_price_changed = compare_prices(price)
    if is_price_changed:
        sendEmail(email=email, app_password=app_password, destiny=destiny, price=price)
    


def get_price(options):
    driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://www.coursera.org/courseraplus/special/latam-spring-2026-40")

        wait = WebDriverWait(driver, 10)

        price_spans =  driver.find_elements(By.CLASS_NAME, "rc-ReactPriceDisplay")
        

        precios_validos = set()

        for span in price_spans:
            texto = span.text.strip()
            print("Raw:", texto)

            # limpiar texto → solo números
            numero = re.sub(r"[^\d]", "", texto)

            if numero:
                precio = int(numero)

                if 2000 <= precio <= 4600:
                    precios_validos.add(precio)

        print("Precios filtrados:", precios_validos)

        if not precios_validos:
            return None

        precio_final = min(precios_validos)

        return precio_final

    except Exception as e:
        print("Error:", e)
        return None

    finally:
        driver.quit()
    
def compare_prices(price):
    pricing = {
        "price": price,
        "date": str(date.today())
    }
    last_price = 0
    if os.path.exists("data.json"):
        try:
            with open("data.json", "r") as f:
                dataset = json.load(f)
        except:
            dataset = []
    else:
        dataset = []
    dataset.append(pricing)
    try: 
        with open("data.json", "w") as f:
            json.dump(dataset,f,indent=4)
    except: 
        print("Ha ocurrido un error durante la escritura de datos")
    dataset_size = len(dataset)
    if dataset_size >= 2:
        last_price = dataset[dataset_size-2]["price"]
    else:
        last_price = 4590
    if price!=last_price:
        return True
    else: 
        return False
        

    
def sendEmail(email, app_password, destiny, price):
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 20px;">
        
        <div style="max-width: 500px; margin: auto; background: white; border-radius: 10px; padding: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
        
        <h2 style="color: #2c3e50; text-align: center;">Price Alert</h2>
        
        <p style="font-size: 16px; color: #555;">
            El precio de <b>Coursera Plus</b> ha cambiado
        </p>

        <div style="text-align: center; margin: 20px 0;">
            <span style="font-size: 28px; color: #27ae60; font-weight: bold;">
            ${price} MXN
            </span>
        </div>

        <p style="text-align: center;">
            <a href="https://www.coursera.org/courseraplus" 
            style="background-color: #3498db; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none;">
            Ver oferta
            </a>
        </p>

        

        <p style="font-size: 12px; color: #999; text-align: center;">
            Correo automatizado
        </p>

        </div>

    </body>
    </html>
    """
    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = " Coursera Price Alert"
    msg["From"] = email
    msg["To"] = destiny
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(email,app_password)
        server.send_message(msg)
        print("El correo ha sido enviado")

if __name__ == "__main__":
    main()