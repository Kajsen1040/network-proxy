import argparse
import base64
import binascii
import http.client
import hmac
import select
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


HOP_BY_HOP_HEADERS = {
	"connection",
	"keep-alive",
	"proxy-authenticate",
	"proxy-authorization",
	"proxy-connection",
	"te",
	"trailer",
	"transfer-encoding",
	"upgrade",
}
MAX_REQUEST_BODY = 10 * 1024 * 1024


class ProxyServer(ThreadingHTTPServer):
	daemon_threads = True


class ProxyHandler(BaseHTTPRequestHandler):
	protocol_version = "HTTP/1.1"
	auth_credentials = None

	def _authorized(self):
		if self.auth_credentials is None:
			return True

		header = self.headers.get("Proxy-Authorization", "")
		scheme, separator, encoded = header.partition(" ")
		if separator and scheme.lower() == "basic":
			try:
				decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
			except (ValueError, UnicodeDecodeError, binascii.Error):
				decoded = ""
			username, separator, password = decoded.partition(":")
			if separator and all(
				hmac.compare_digest(value, expected)
				for value, expected in (
					(username, self.auth_credentials[0]),
					(password, self.auth_credentials[1]),
				)
			):
				return True

		self.send_response(407, "Proxy Authentication Required")
		self.send_header("Proxy-Authenticate", 'Basic realm="Local Wi-Fi Proxy"')
		self.send_header("Content-Length", "0")
		self.end_headers()
		return False

	def do_CONNECT(self):
		if not self._authorized():
			return
		host, separator, port_text = self.path.rpartition(":")
		if not separator or not host or port_text != "443":
			self.send_error(403, "CONNECT is allowed only to port 443")
			return
		host = host.strip("[]")

		try:
			port = int(port_text)
			upstream = socket.create_connection((host, port), timeout=10)
		except (OSError, ValueError) as error:
			self.send_error(502, f"Unable to connect to upstream server: {error}")
			return

		self.send_response(200, "Connection Established")
		self.end_headers()
		self._tunnel(upstream)

	def do_GET(self):
		self._forward_request()

	def do_HEAD(self):
		self._forward_request()

	def do_POST(self):
		self._forward_request()

	def do_PUT(self):
		self._forward_request()

	def do_PATCH(self):
		self._forward_request()

	def do_DELETE(self):
		self._forward_request()

	def do_OPTIONS(self):
		self._forward_request()

	def _forward_request(self):
		if not self._authorized():
			return
		try:
			target = urlsplit(self.path)
		except ValueError:
			self.send_error(400, "Malformed target URL")
			return
		if (
			target.scheme not in {"http", ""}
			or not target.hostname
			or target.username is not None
			or target.password is not None
		):
			self.send_error(400, "Use an absolute HTTP URL")
			return

		try:
			port = target.port or 80
		except ValueError:
			self.send_error(400, "Invalid target port")
			return
		path = target.path or "/"
		if target.query:
			path += "?" + target.query
		body = None
		content_length = self.headers.get("Content-Length")
		if content_length is not None:
			try:
				body_length = int(content_length)
			except ValueError:
				self.send_error(400, "Invalid Content-Length")
				return
			if body_length < 0 or body_length > MAX_REQUEST_BODY:
				self.send_error(413, "Request body is too large")
				return
			body = self.rfile.read(body_length)
		elif self.headers.get("Transfer-Encoding"):
			self.send_error(501, "Chunked client requests are not supported")
			return

		headers = {
			key: value
			for key, value in self.headers.items()
			if key.lower() not in HOP_BY_HOP_HEADERS and key.lower() != "host"
		}
		headers["Host"] = target.netloc
		headers["Connection"] = "close"

		connection = None
		try:
			connection = http.client.HTTPConnection(target.hostname, port, timeout=15)
			connection.request(self.command, path, body=body, headers=headers)
			response = connection.getresponse()
		except (OSError, http.client.HTTPException) as error:
			self.send_error(502, f"Unable to fetch upstream resource: {error}")
			return

		try:
			self.send_response(response.status, response.reason)
			response_length = response.getheader("Content-Length")
			for key, value in response.getheaders():
				if key.lower() not in HOP_BY_HOP_HEADERS and key.lower() != "content-length":
					self.send_header(key, value)
			if response_length is not None:
				self.send_header("Content-Length", response_length)
			self.send_header("Connection", "close")
			self.end_headers()
			if self.command != "HEAD":
				while chunk := response.read(65536):
					self.wfile.write(chunk)
		finally:
			if connection is not None:
				connection.close()

	def _tunnel(self, upstream):
		sockets = [self.connection, upstream]
		try:
			while True:
				readable, _, exceptional = select.select(sockets, [], sockets, 30)
				if exceptional or not readable:
					return
				for source in readable:
					data = source.recv(65536)
					if not data:
						return
					destination = upstream if source is self.connection else self.connection
					destination.sendall(data)
		finally:
			upstream.close()

	def log_message(self, format_string, *args):
		return


def main():
	parser = argparse.ArgumentParser(description="Local HTTP/HTTPS forward proxy")
	parser.add_argument("--host", default="127.0.0.1", help="bind address (default: 127.0.0.1)")
	parser.add_argument("--port", type=int, default=8080, help="port to bind (default: 8080)")
	parser.add_argument("--auth-file", type=Path, help="file containing username:password; required off localhost")
	args = parser.parse_args()
	loopback_hosts = {"127.0.0.1", "localhost", "::1"}
	if args.host not in loopback_hosts and args.auth_file is None:
		parser.error("--auth-file is required when binding beyond localhost")

	auth_credentials = None
	if args.auth_file is not None:
		try:
			credentials = args.auth_file.read_text(encoding="utf-8").strip()
		except OSError as error:
			parser.error(f"unable to read --auth-file: {error}")
		username, separator, password = credentials.partition(":")
		if not separator or not username or not password:
			parser.error("--auth-file must contain username:password")
		auth_credentials = (username, password)
	ProxyHandler.auth_credentials = auth_credentials

	with ProxyServer((args.host, args.port), ProxyHandler) as server:
		print(f"Proxy listening on http://{args.host}:{args.port}")
		try:
			server.serve_forever()
		except KeyboardInterrupt:
			print("\nStopping proxy")


if __name__ == "__main__":
	main()
