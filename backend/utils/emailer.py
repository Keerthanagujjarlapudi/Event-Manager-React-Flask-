from flask_mail import Mail, Message

mail = Mail()

def init_mail(app):
    mail.init_app(app)

def send_email(to_email: str, subject: str, body: str, html: str = None):
    if not to_email:
        raise ValueError("to_email is required")

    msg = Message(subject=subject, recipients=[to_email])
    msg.body = body
    if html:
        msg.html = html

    mail.send(msg)
