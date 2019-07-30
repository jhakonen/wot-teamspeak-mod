import asynchat
import asyncore
import socket

class HTTPServer(asyncore.dispatcher):

    def __init__(self, sock_map):
        asyncore.dispatcher.__init__(self, map=sock_map)
        self._sock_map = sock_map
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(('localhost', 0))
        self.listen(5)

    def set_response(self, code, message, body):
        self._response = (code, message, body)

    def get_url(self):
        return "http://%s:%d/" % self.socket.getsockname()

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            handler = HTTPHandler(sock, self._sock_map, self._response)

class HTTPHandler(asynchat.async_chat):
    def __init__(self, sock, sock_map, response):
        asynchat.async_chat.__init__(self, sock=sock, map=sock_map)
        self._response = response
        self.set_terminator("\r\n\r\n")

    def collect_incoming_data(self, data):
        pass

    def found_terminator(self):
        self.push("HTTP/1.0 %d %s\r\n" % self._response[:2])
        self.push("Content-Length: %d\r\n" % len(self._response[2]))
        self.push("\r\n")
        self.push(self._response[2])
        self.close_when_done()
