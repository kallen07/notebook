#!/usr/bin/python3

''' Create GitStore server so Jupyter Notebook can connect from a Browser '''

# import SimpleHTTPServer
from http.server import BaseHTTPRequestHandler, HTTPServer
from git_store import *
# import SocketServer
# import os.path
# import sys
from sys import argv, stderr
import json
import os


class GitStoreHandler(BaseHTTPRequestHandler):
    ''' HTTP interface to GitStore operations. Initialized for each Notebook
        Session.
    '''

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', 'http://localhost:8888')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        print('in do_GET')
        possible_name = self.path.strip('/')+'.html'
        print('possible name: {}'.format(possible_name))
        self._set_headers()
        self.wfile.write('Got path: {}'.format(self.path).encode())

        # return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        print('in do_POST')
        self.data_string = self.rfile.read(int(self.headers['Content-Length']))
        self.data_json = json.loads(self.data_string.decode())
        print('Got data string: {}'.format(self.data_string))
        print('Got path: {}'.format(self.path))
        possible_name = self.path.strip('/')+'.html'
        print('possible name: {}'.format(possible_name))

        if self.path == '/new_notebook':
            notebook_url = self.data_json['dir_path']
            full_path = os.path.join(notebook_dir, notebook_url)
            print('Url: {}. Full: {}'.format(notebook_url, full_path))
            nb = open_notebook(full_path)
            repo = open_repo(notebook_dir)
            update_repo(repo, nb)
            repo.close()
        elif self.path == '/save_notebook':
            nb_path = self.data_json['nb_path']
            nb_contents = self.data_json['nb_contents']
            full_path = os.path.join(notebook_dir, nb_path)
            nb = open_notebook(full_path)
            repo = open_repo(notebook_dir)
            update_repo(repo, nb)
            repo.close()
        elif self.path == '/restore_checkpoint':
            nb_path = self.data_json['nb_path']
            checkpoint = self.data_json['checkpoint']
            full_path = os.path.join(notebook_dir, nb_path)
            print('Checkpoint: {}'.format(checkpoint))
            repo = open_repo(notebook_dir)
            # TODO: Revision is hardcoded for now
            checkpoint = 'ae51092b34a81366cdaf36e51e922d2aa36eca18'
            checkout_revision(repo, checkpoint)
            write_notebook(repo, full_path)


        self._set_headers()
        self.send_response(200)
        self.end_headers()

        # data = simplejson.loads(self.data_string)
        # with open('test123456.json', 'w') as outfile:
        #     simplejson.dump(data, outfile)
        # print '{}'.format(data)
        # f = open('for_presen.py')
        # self.wfile.write(f.read())
        #self.wfile.write('Got your data!'.encode())


def start_git_store():
    port = 8000
    global notebook_dir
    if len(argv) > 1:
        try:
            p = int(argv[1])
            port = p
            notebook_dir = argv[2]
        except ValueError:
            print('port value provided must be an integer')

    print('serving on port {0}'.format(port), file=stderr)
    # server = SocketServer.TCPServer(('0.0.0.0', port), Handler)
    httpd = HTTPServer(('0.0.0.0', port), GitStoreHandler)
    httpd.serve_forever()


if __name__ == '__main__':
    start_git_store()