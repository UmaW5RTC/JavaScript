# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import current_app
import sendgrid


def sendmail(to, subject, html, from_name='DQ World'):
    if current_app.config.get("SENDGRID_USERNAME") and current_app.config.get("SENDGRID_PASSWORD"):
        try:
            sg = sendgrid.SendGridClient(current_app.config["SENDGRID_USERNAME"],
                                         current_app.config["SENDGRID_PASSWORD"],
                                         raise_errors=True)

            message = sendgrid.Mail()
            message.add_to(to)
            message.set_subject(subject)
            message.set_html(html)
            message.set_from(from_name + ' <' + current_app.config.get('MANDRILL_DEFAULT_FROM', 'admin@dqworld.net') + '>')
            sg.send(message)
        except Exception:
            sendmail_mandrill(to, subject, html, from_name)
    else:
        sendmail_mandrill(to, subject, html, from_name)


def sendmail_mandrill(to, subject, html, from_name):
    current_app.mandrill.send_email(to=[{'email': to}],
                                    subject=subject,
                                    html=html,
                                    from_name=from_name)
