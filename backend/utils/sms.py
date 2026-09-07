from config import Config

def send_sms(to_phone: str, message: str):
    # Mock mode (default)
    if Config.SMS_PROVIDER == "mock":
        print(f"[MOCK SMS] To: {to_phone} | {message}")
        return

    # Twilio mode (optional)
    if Config.SMS_PROVIDER == "twilio":
        try:
            from twilio.rest import Client
        except ImportError:
            raise RuntimeError("Install twilio: pip install twilio")

        if not all([Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN, Config.TWILIO_FROM]):
            raise RuntimeError("Twilio env not configured")

        client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=Config.TWILIO_FROM,
            to=to_phone
        )
        return

    raise RuntimeError(f"Unknown SMS_PROVIDER: {Config.SMS_PROVIDER}")
