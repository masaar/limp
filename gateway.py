from config import Config

from typing import Literal, List, TypedDict, Any

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

import smtplib

def email_gateway(
			subject: str,
			addr_to: str,
			content: str,
			content_format: Literal['html', 'plain']='html',
			files: List[TypedDict('GATEWAY_EMAIL_FILES', name=str, content=Any)]=[],
			email_auth: TypedDict('GATEWAY_EMAIL_AUTH', server=str, username=str, password=str)=None
		):
	if not email_auth:
		email_auth = Config.email_auth
	if type(addr_to) == str:
		addr_to = [addr_to]
	addr_to = COMMASPACE.join(addr_to)
	
	msg = MIMEMultipart()
	msg['From'] = email_auth['username']
	msg['To'] = addr_to
	msg['Date'] = formatdate(localtime=True)
	msg['Subject'] = subject

	msg.attach(MIMEText(content, content_format))

	for file in files:
		part = MIMEApplication(file['content'], Name=file['name'])
		part['Content-Disposition'] = f'attachment; filename="{file["name"]}"'
		msg.attach(part)

	smtp = smtplib.SMTP_SSL(email_auth['server'])
	smtp.login(email_auth['username'], email_auth['password'])
	smtp.sendmail(email_auth['username'], addr_to, msg.as_string())
	smtp.close()

class Gateway:

	@staticmethod
	def send(*, gateway: str, **kwargs):
		if gateway == 'email':
			return email_gateway(**kwargs)
		else:
			return Config.gateways[gateway](**kwargs)