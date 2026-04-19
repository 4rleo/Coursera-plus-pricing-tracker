import smtplib
from datetime import date
import os, json, re
import requests
from email.mime.text import MIMEText

def main():
    email = os.getenv("GMAIL_USER")
    app_password = os.getenv("GMAIL_PASSWORD")
    destiny = "rodriguezcervantessebastian30@gmail.com"
    
    api_url = "Thttps://api.stripe.com/v1/elements/sessions?client_secret=pi_3TNpPbBEfO1jc2fn05JSJTfJ_secret_2FcOJ5pC70eaxCga7Gh2zI0id&key=pk_live_51MZeRpBEfO1jc2fnXqfGeAjDZ83rmeS3YQu3G1NYIBWUvlsIthQwVBTO52HMoB3ORJpbsYBqFiKLw0UIqsAhbQK100PzRQTfLV&elements_init_source=stripe.elements&referrer_host=www.coursera.org&stripe_js_id=ede13da8-7229-4982-a03f-4bdb111312f5&locale=es-LA&expand[0]=payment_method_preference.payment_intent.payment_method&type=payment_intent" 
    
    price = get_price(api_url)
    print(f"Precio detectado: {price}")
    
    if price is not None:
        is_price_changed = update_json_and_check_diff(price)
        if is_price_changed:
            print("El precio cambió. Enviando correo...")
            sendEmail(email=email, app_password=app_password, destiny=destiny, price=price)
    else:
        print("No se pudo obtener el precio.")

def get_price(url):
    try:
        cookies_raw = os.getenv("COURSERA_COOKIES")
        if not cookies_raw:
            return None
            
        cookies_list = json.loads(cookies_raw)
        cookies_dict = {c['name']: c['value'] for c in cookies_list}

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "es-MX,es;q=0.9",
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.coursera.org/courseraplus"
        }

        response = requests.get(url, headers=headers, cookies=cookies_dict, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            payment_intent = data.get("payment_method_preference", {}).get("payment_intent", {})
            amount_in_cents = payment_intent.get("amount")
            currency = payment_intent.get("currency")

            if amount_in_cents and currency == "mxn":
                return amount_in_cents / 100
        return None

    except Exception as e:
        print(f"Error: {e}")
        return None

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
        return
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 500px; margin: auto; border: 1px solid #eee; padding: 20px; border-radius: 10px;">
            <h2 style="color: #2c3e50;">🚀 ¡Oportunidad en Coursera Plus!</h2>
            <p style="font-size: 16px;">El precio actualizado es de: <b style="color: #27ae60;">${price} MXN</b></p>
            <div style="margin-top: 20px;">
                <a href="https://www.coursera.org/courseraplus" 
                   style="background: #2980b9; color: white; padding: 12px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                   Ir a Coursera Plus
                </a>
            </div>
            <p style="color: #7f8c8d; font-size: 12px; margin-top: 30px;">Aviso automático.</p>
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
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
