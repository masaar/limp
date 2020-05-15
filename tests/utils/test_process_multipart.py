from limp.utils import process_multipart

from typing import Literal
import pytest


@pytest.fixture
def multipart_CRLF():
	# [DOC] CRLF, \r\n, DOS
	rfile = b'''\r\n-----------------------------9051914041544843365972754266\r\ncontent-Disposition: form-data; name="text"\r\n\r\ntext default\r\n-----------------------------9051914041544843365972754266\r\nContent-disposition: form-data; name=file1; filename=a.txt\r\nContent-type: text/plain\r\n\r\nMultiline.\r\nContent of a.txt.\r\n\r\n-----------------------------9051914041544843365972754266\r\ncontent-disposition: form-data; name="file2"; filename="a.html"\r\nContent-Type: text/html\r\n\r\n<!DOCTYPE html>\r\n\t<head>\r\n\t\t<title>Content of a.html.</title>\r\n\t</head>\r\n\t<body>\r\n\t</body>\r\n</html>\r\n\r\n-----------------------------9051914041544843365972754266--'''

	return (rfile, b'---------------------------9051914041544843365972754266')


@pytest.fixture
def multipart_LF(multipart_CRLF):
	# [DOC] LF, \n, UNIX
	return (
		multipart_CRLF[0].replace(b'\r\n', b'\n'),
		b'---------------------------9051914041544843365972754266',
	)


def test_process_multipart_CRLF(multipart_CRLF):
	rfile, boundary = multipart_CRLF
	multipart = process_multipart(rfile=rfile, boundary=boundary)

	assert len(list(multipart.keys())) == 3
	assert multipart[b'text'][3] == b'text default'
	assert multipart[b'file1'][3] == b'Multiline.\nContent of a.txt.'
	assert (
		multipart[b'file2'][3]
		== b'<!DOCTYPE html>\n\t<head>\n\t\t<title>Content of a.html.</title>\n\t</head>\n\t<body>\n\t</body>\n</html>'
	)


def test_process_multipart_LF(multipart_LF):
	rfile, boundary = multipart_LF
	multipart = process_multipart(rfile=rfile, boundary=boundary)

	assert len(list(multipart.keys())) == 3
	assert multipart[b'text'][3] == b'text default'
	assert multipart[b'file1'][3] == b'Multiline.\nContent of a.txt.'
	assert (
		multipart[b'file2'][3]
		== b'<!DOCTYPE html>\n\t<head>\n\t\t<title>Content of a.html.</title>\n\t</head>\n\t<body>\n\t</body>\n</html>'
	)
