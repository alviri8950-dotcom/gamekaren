import os
import ssl
from wsgiref.simple_server import make_server, WSGIServer
from socketserver import ThreadingMixIn

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler

application = StaticFilesHandler(get_wsgi_application())

CERT_FILE = r"C:\mkcert\192.168.100.220+2.pem"
KEY_FILE = r"C:\mkcert\192.168.100.220+2-key.pem"

class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True

if __name__ == '__main__':
    httpd = make_server('0.0.0.0', 8000, application, server_class=ThreadingWSGIServer)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    print("HTTPS server running at https://0.0.0.0:8000/")
    httpd.serve_forever()