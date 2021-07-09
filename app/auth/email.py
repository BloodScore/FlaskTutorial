from flask import current_app, render_template
from app.email import send_mail


def send_password_reset_mail(user):
    token = user.get_reset_password_token()
    send_mail(
        '[Microblog] Reset Your Password',
        sender=current_app.config['ADMINS'][0],
        recipients=[user.email],
        text_body=render_template('email/reset_password_mail.txt', user=user, token=token),
        html_body=render_template('email/reset_password_mail.html', user=user, token=token)
    )
