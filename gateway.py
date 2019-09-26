from config import Config

from twilio.rest import Client

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
import smtplib

class Gateway:

	@classmethod
	def send_sms(cls, to, body):
		account_sid = Config.sms_auth['sid']
		auth_token = Config.sms_auth['token']
		client = Client(account_sid, auth_token)
		message = client.messages.create(
			body=body,
			from_=Config.sms_auth['number'],
			to=to
		)
		return message
	
	@classmethod
	def send_email(cls, subject, addr_to, content, content_format='html', files=[]):
		if type(addr_to) == str:
			addr_to = [addr_to]
		addr_to = COMMASPACE.join(addr_to)
		
		msg = MIMEMultipart()
		msg['From'] = Config.email_auth['username']
		msg['To'] = addr_to
		msg['Date'] = formatdate(localtime=True)
		msg['Subject'] = subject

		msg.attach(MIMEText(content, content_format))

		for file in files:
			part = MIMEApplication(file['content'], Name=file['name'])
			part['Content-Disposition'] = 'attachment; filename="{}"'.format(file['name'])
			msg.attach(part)

		email_server = Config.email_auth['server']
		email_username = Config.email_auth['username']
		email_password = Config.email_auth['password']

		smtp = smtplib.SMTP_SSL(email_server)
		smtp.login(email_username, email_password)
		smtp.sendmail(Config.email_auth['username'], addr_to, msg.as_string())
		smtp.close()