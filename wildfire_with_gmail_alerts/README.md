
# 🔔 Alerts via Gmail SMTP

You can configure the system to send wildfire risk alerts via **Gmail SMTP** — no paid services needed.

## 1. Enable Gmail App Password
1. Enable **2-Step Verification** in your Google account.  
2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords).  
3. Create a new app password for **Mail → Other (WildfireAlerts)**.  
4. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`).  

## 2. Configure `config.yaml`
Edit `config.yaml` in the project root:

```yaml
alerts:
  threshold: 0.6
  recipients:
    email:
      - "your_email@gmail.com"
      - "1234567890@carrier-sms-gateway.com"   # optional: send SMS via email-to-SMS gateway

gmail:
  from_email: "your_email@gmail.com"
  app_password: "abcdefghijklmnop"   # your 16-char app password (no spaces)
```

- **recipients.email** → list of email addresses (can include carrier SMS gateways).  
- **from_email** → the Gmail account you generated the App Password for.  
- **app_password** → the App Password (not your regular Gmail password).  

## 3. Run the Alerting Script
After you’ve computed SHAP predictions (`features_with_shap.parquet`), run:

```bash
python src/alerts/alerting.py
```

- If today’s wildfire risk exceeds the threshold (default `0.6`), Gmail will send alerts to all configured recipients.  
- To test, you can temporarily set `threshold: 0.0` in `config.yaml` so alerts are always sent.  

## 4. Troubleshooting
- If Gmail blocks the login, check your Google account security notifications.  
- Ensure you are using an **App Password**, not your normal Gmail password.  
- Email-to-SMS gateways vary by carrier (e.g., for Verizon US → `number@vtext.com`).  

✅ With this setup, the system sends alerts **100% free via Gmail SMTP**.  
