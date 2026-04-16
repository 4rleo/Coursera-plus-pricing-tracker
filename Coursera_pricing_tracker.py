import smtplib
from datetime import date
import os, json, re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from email.mime.text import MIMEText
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

def main():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    email = os.getenv("GMAIL_USER")
    app_password = os.getenv("GMAIL_PASSWORD")
    destiny = "rodriguezcervantessebastian30@gmail.com"
    
    price = get_price(options)
    print(f"Precio detectado: {price}")
    
    if price:
        is_changed = update_json(price)
        if is_changed:
            send_email(email, app_password, destiny, price)
    else:
        print("No se pudo obtener el precio.")

def get_price(options):
    options.binary_location = os.getenv("CHROME_BIN")
    service = Service(os.getenv("CHROMEDRIVER_BIN"))
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get("https://www.coursera.org/courseraplus/special/latam-spring-2026-40")
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "rc-ReactPriceDisplay")))
        
        price_spans = driver.find_elements(By.CLASS_NAME, "rc-ReactPriceDisplay")
        valid_prices = set()

        for span in price_spans:
            text = span.text.strip()
            num = re.sub(r"[^\d]", "", text)
            if num:
                p = int(num)
                if 2000 <= p <= 5000:
                    valid_prices.add(p)

        return min(valid_prices) if valid_prices else None
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        driver.quit()

def update_json(price):
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
    
    return price != last_price

def send_email(user, pwd, to, price):
    if not user or not pwd:
        return

    html = f"""
    <html>
    <body style="font-family: Arial; padding: 20px;">
        <div style="max-width: 500px; margin: auto; border: 1px solid #eee; padding: 20px;">
            <h2>Alerta de Precio</h2>
            <p>Coursera Plus: <b>${price} MXN</b></p>
            <a href="https://www.coursera.org/courseraplus" style="background: #3498db; color: white; padding: 10px; text-decoration: none;">Ver Oferta</a>
        </div>
    </body>
    </html>
    """
    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = "Coursera Price Alert"
    msg["From"] = user
    msg["To"] = to

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(user, pwd)
            server.send_message(msg)
    except Exception as e:
        print(f"Email error: {e}")

if __name__ == "__main__":
    main()
