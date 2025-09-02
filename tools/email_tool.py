import sendgrid
import os
from sendgrid.helpers.mail import Mail, Email, To, Content


def send_email():
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    from_email = Email(os.environ.get('PERSONAL_EMAIL'))  # Change to your verified sender
    to_email = To(os.environ.get('PERSONAL_EMAIL'))  # Change to your recipient
    content = Content("text/plain", "This is an important test email")
    mail = Mail(from_email, to_email, "Test email", content).get()
    response = sg.client.mail.send.post(request_body=mail)
    print(response.status_code)