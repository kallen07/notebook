import SimpleHTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import os.path
import sys

class GitStoreHandler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', 'http://localhost:8888')
        self.send_header('Content-type', 'text/html')
        self.end_headers()
    def do_GET(self):   
        print "in do_GET!"         
        possible_name = self.path.strip("/")+'.html'
        self._set_headers()
        self.wfile.write("Got path: " + self.path)

        # return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
    def do_POST(self):
        self._set_headers()
        print "in post method"
        self.data_string = self.rfile.read(int(self.headers['Content-Length']))
        print "Got data string: ", self.data_string
        print "Got path: " , self.path

        self.send_response(200)
        self.end_headers()

        # data = simplejson.loads(self.data_string)
        # with open("test123456.json", "w") as outfile:
        #     simplejson.dump(data, outfile)
        # print "{}".format(data)
        # f = open("for_presen.py")
        # self.wfile.write(f.read())
        self.wfile.write("Got your data!")

Handler = GitStoreHandler

port = 8000
if len(sys.argv) > 1:
    try:
        p = int(sys.argv[1])
        port = p
    except ValueError:
        print "port value provided must be an integer"

print >> sys.stderr, "serving on port {0}".format(port)
#server = SocketServer.TCPServer(('0.0.0.0', port), Handler)
httpd = HTTPServer(('0.0.0.0', port), Handler)
httpd.serve_forever()