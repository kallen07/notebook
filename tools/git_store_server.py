#!/usr/bin/python3

''' Create GitStore server so Jupyter Notebook can connect from a Browser '''

from http.server import BaseHTTPRequestHandler, HTTPServer
from tools.git_store import *
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

    def do_POST(self):
        print('in do_POST')
        self.data_string = self.rfile.read(int(self.headers['Content-Length']))
        self.data_json = json.loads(self.data_string.decode())
        print('Got data string: {}'.format(self.data_string))
        print('Got path: {}'.format(self.path))

        if self.path == '/new_notebook':
            print('in new_notebook')

            nb_name = self.data_json['nb_name']
            print('nb_name: {}'.format(nb_name))

            save_notebook(nb_dir, nb_name)

        elif self.path == '/save_notebook':
            print('in save_notebook')

            nb_name = self.data_json['nb_name']
            print('nb_name: {}'.format(nb_name))

            save_notebook(nb_dir, nb_name)

        elif self.path == '/restore_snapshot':
            print('in restore_snapshot')

            nb_name = self.data_json['nb_name']
            print('nb_name: {}'.format(nb_name))

            print('nb_path: {}'.format(get_nb_path(nb_dir, nb_name)))

            rev = self.data_json['rev']
            print('rev: {}'.format(rev))

            restore_snapshot(nb_dir, nb_name, rev)

        elif self.path == '/create_tag':
            print('in create_tag')

            nb_name = self.data_json['nb_name']
            print('nb_name: {}'.format(nb_name))

            tag = self.data_json['tag_name']
            print('tag_name: {}'.format(tag))

            save_notebook(nb_dir, nb_name, tag_name=tag)

        elif self.path == '/rename_notebook':
            print('in rename_notebook')

            old_name = self.data_json['old_name']
            print('old_name: {}'.format(old_name))

            new_name = self.data_json['new_name']
            print('new_name: {}'.format(new_name))

            rename_notebook(nb_dir, old_name, new_name)

        else:
            print('Unrecognized path: {0}'.format(self.path))

        self._set_headers()
        self.send_response(200)
        self.end_headers()

        # data = simplejson.loads(self.data_string)
        # with open('test123456.json', 'w') as outfile:
        #     simplejson.dump(data, outfile)
        # print '{}'.format(data)
        # f = open('for_presen.py')
        # self.wfile.write(f.read())
        # self.wfile.write('Got your data!'.encode())


def start_git_store():
    port = 8000
    global nb_dir
    if len(argv) > 1:
        try:
            p = int(argv[1])
            port = p
            nb_dir = argv[2]
        except ValueError:
            print('port value provided must be an integer')

    print('serving on port {0}'.format(port), file=stderr)
    httpd = HTTPServer(('0.0.0.0', port), GitStoreHandler)
    httpd.serve_forever()


if __name__ == '__main__':
    start_git_store()
