#!/usr/bin/python3

''' Create GitStore server so Jupyter Notebook can connect from a Browser '''

from http.server import BaseHTTPRequestHandler, HTTPServer
from json import dumps, loads
from logging import Formatter, INFO, StreamHandler, getLogger
from sys import argv
from tools.git_store import *


class GitStoreHandler(BaseHTTPRequestHandler):
    ''' HTTP interface to GitStore operations. Initialized for each Notebook
        Session.
    '''

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', 'http://localhost:8888')
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        log.info('in do_GET, path: {}'.format(self.path))

        self._set_headers()
        self.wfile.write(dumps({'Hello': 'World', 'path': self.path}).encode())

    def do_POST(self):
        self.data_string = self.rfile.read(int(self.headers['Content-Length']))
        self.data_json = loads(self.data_string.decode())

        log.info('in do_POST, path: {0}, data: {1}'
                 .format(self.path, self.data_json))

        if self.path == '/new_notebook':
            nb_name = self.data_json['nb_name']

            log.info('in new_notebook, nb_name: {}'.format(nb_name))

            save_notebook(nb_dir, nb_name)

        elif self.path == '/save_notebook':
            nb_name = self.data_json['nb_name']

            log.info('in save_notebook, nb_name: {}'.format(nb_name))

            save_notebook(nb_dir, nb_name)

        elif self.path == '/restore_snapshot':
            nb_name = self.data_json['nb_name']
            rev = self.data_json['rev']

            log.info('in restore_snapshot, nb_name: {0}, rev: {1}'
                     .format(nb_name, rev))

            restore_snapshot(nb_dir, nb_name, rev)

        elif self.path == '/rename_notebook':
            old_name = self.data_json['old_name']
            new_name = self.data_json['new_name']

            log.info('in rename_notebook: old_name: {0}, new_name: {1}'
                     .format(old_name, new_name))

            rename_notebook(nb_dir, old_name, new_name)

        elif self.path == '/create_tag':
            nb_name = self.data_json['nb_name']
            tag = self.data_json['tag_name']

            log.info('in create_tag, nb_name: {0}, tag_name: {1}'
                     .format(nb_name, tag))

            save_notebook(nb_dir, nb_name, tag_name=tag)

        elif self.path == '/get_tags':
            nb_name = self.data_json['nb_name']
            tags = get_tag_list(nb_dir, nb_name)

            log.info('in get_tags, nb_name: {0}, tags: {1}'
                     .format(nb_name, tags))

            self.wfile.write(dumps(tags).encode())

        elif self.path == '/delete_notebook':
            nb_name = self.data_json['nb_name']

            log.info('in delete_notebook, nb_name: {}'.format(nb_name))

            delete_notebook(nb_dir, nb_name)

        else:
            log.warn('Unrecognized path: {0}'.format(self.path))

        self._set_headers()
        self.send_response(200)
        self.end_headers()


def start_git_store():
    #
    # Setup logging
    #
    global log
    log = getLogger(__name__)
    log.setLevel(INFO)
    handler = StreamHandler()
    formatter = Formatter('[%(levelname)s %(asctime)-15s] %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)

    #
    # Read input, assign port and notebook root directory
    #
    port = 8000
    global nb_dir
    if len(argv) > 1:
        try:
            p = int(argv[1])
            port = p
            nb_dir = argv[2]
        except ValueError:
            log.warn('port value provided must be an integer')

    log.info('serving on port {0}'.format(port))
    httpd = HTTPServer(('0.0.0.0', port), GitStoreHandler)
    httpd.serve_forever()


if __name__ == '__main__':
    start_git_store()
