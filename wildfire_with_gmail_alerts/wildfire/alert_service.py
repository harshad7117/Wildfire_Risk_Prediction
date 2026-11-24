import os
import yaml
import smtplib
from email.mime.text import MIMEText

# Detect absolute path (works even if Streamlit runs from a different folder)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE_DIR, "config.yaml")


def load_config():
    """
    Load alert configuration from config.yaml.
    """
    if not os.path.exists(CONFIG):
        raise FileNotFoundError(f"❌ Config file not found at: {CONFIG}")

    with open(CONFIG, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def send_email_gmail(tolist, subject, body, cfg):
    """
    Send an email using Gmail SMTP with App Password.
    """
    from_email = cfg["gmail"]["from_email"]
    password = cfg["gmail"]["app_password"]

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = ", ".join(tolist)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(from_email, password)
            server.sendmail(from_email, tolist, msg.as_string())
            print(f"✅ Email sent to: {tolist}")
    except Exception as e:
        print(f"⚠️ Failed to send email: {e}")


def send_alert(lat, lon, probability):
    """
    Send wildfire alert via Email and SMS (through email-to-SMS gateways).
    """
    cfg = load_config()

    recipients_email = cfg.get("alerts", {}).get("recipients", {}).get("email", [])
    recipients_sms = cfg.get("alerts", {}).get("recipients", {}).get("sms", [])

    subject = "🚨 Wildfire High Risk Alert"
    body = (
        f"🔥 ALERT: High Risk of Wildfire Detected!\n\n"
        f"📍 Location: Latitude {lat:.2f}, Longitude {lon:.2f}\n"
        f"🔥 Risk Probability: {probability:.2f}\n\n"
        "⚠️ Please take immediate precautions and notify local authorities."
    )

    if recipients_email:
        send_email_gmail(recipients_email, subject, body, cfg)

    if recipients_sms:
        send_email_gmail(recipients_sms, subject, body, cfg)
        print(f"📲 SMS Alerts sent via Email-to-SMS: {recipients_sms}")
