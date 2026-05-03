import json
import os
import smtplib
from email.mime.text import MIMEText
from datetime import date

def send_email(subject, body):
    user = os.getenv("GMAIL_USER")
    pw = os.getenv("GMAIL_PASSWORD")
    dest = os.getenv("GMAIL_ERROR_DESTINY")
    
    if not user or not dest:
        return

    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = dest

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(user, pw)
            server.send_message(msg)
    except Exception as e:
        print(f"Error enviando correo de comparador: {e}")

def main():
    cloud_file = "data.json"
    local_file = "data_local.json"

    # Verificamos que ambos archivos existan
    if not os.path.exists(cloud_file) or not os.path.exists(local_file):
        print("Faltan archivos para comparar.")
        return

    try:
        with open(cloud_file, "r") as f:
            cloud_data = json.load(f)
            # Si es una lista (por tu save_price anterior), tomamos el último
            cloud_entry = cloud_data[-1] if isinstance(cloud_data, list) else cloud_data
            
        with open(local_file, "r") as f:
            local_data = json.load(f)
            local_entry = local_data[-1] if isinstance(local_data, list) else local_data

        cloud_price = cloud_entry.get("price")
        local_price = local_entry.get("price")

        if cloud_price != local_price:
            print(f"Diferencia detectada: Nube {cloud_price} vs Local {local_price}")
            
            subject = f"ALERTA: Discrepancia detectada — {date.today()}"
            body = f"""
            <h3>Diferencia de precios detectada</h3>
            <p>El script de <b>GitHub Actions</b> detectó: <b>${cloud_price} MXN</b></p>
            <p>El script <b>Local</b> detectó: <b>${local_price} MXN</b></p>
            <br>
            <p><i>Se procederá a corregir data.json usando el valor local.</i></p>
            """
            send_email(subject, body)

            # Corregimos el precio de la nube para que coincida con el local
            if isinstance(cloud_data, list):
                cloud_data[-1]["price"] = local_price
                cloud_data[-1]["corrected"] = True
            else:
                cloud_data["price"] = local_price
                cloud_data["corrected"] = True

            with open(cloud_file, "w") as f:
                json.dump(cloud_data, f, indent=4)
        else:
            print("Los precios coinciden. No se requiere corrección.")

    except Exception as e:
        print(f"Error en el proceso de comparación: {e}")

if __name__ == "__main__":
    main()
