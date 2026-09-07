from flask_mail import Mail, Message

mail = Mail()

def init_mail(app):
    mail.init_app(app)

def send_registration_email(to_email: str, subject: str, html_body: str):
    """
    Sends email. Call this after registration.
    """
    msg = Message(subject=subject, recipients=[to_email])
    msg.html = html_body
    mail.send(msg)
