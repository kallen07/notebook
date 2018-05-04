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
            notebook_url = self.data_json['dir_path']
            full_path = os.path.join(notebook_dir, notebook_url)
            print('Url: {}. Full: {}'.format(notebook_url, full_path))
            nb = open_notebook(full_path)
            repo = open_repo(notebook_dir)
            update_repo(repo, nb)
            repo.close()
        elif self.path == '/save_notebook':
            print('in save_notebook')

            nb_path = self.data_json['nb_path']
            print('nb_path: {}'.format(nb_path))

            repo_path = self.data_json['repo_path']
            print('repo_path: {}'.format(repo_path))

            save_notebook(nb_path, repo_path)

        elif self.path == '/restore_checkpoint':
            print('in restore_checkpoint')

            nb_path = self.data_json['nb_path']
            print('nb_path: {}'.format(nb_path))

            repo_path = self.data_json['repo_path']
            print('repo_path: {}'.format(repo_path))

            checkpoint = self.data_json['checkpoint']
            print('checkpoint: {}'.format(checkpoint))

            repo = open_repo(repo_path)

            logs = get_log(repo)
            for log in logs:
                print('commit: {0}:{1}'.format(log.message, log.name_rev))

            checkout_revision(repo, checkpoint)
            write_notebook(repo, nb_path)
            repo.close()
        elif self.path == '/create_tag':
            print('in create_tag')

            nb_path = self.data_json['nb_path']
            print('nb_path: {}'.format(nb_path))

            repo_path = self.data_json['repo_path']
            print('repo_path: {}'.format(repo_path))

            tag = self.data_json['tag_name']
            print('tag_name: {}'.format(tag))

            save_notebook(nb_path, repo_path, tag_name=tag)
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
    global notebook_dir
    if len(argv) > 1:
        try:
            p = int(argv[1])
            port = p
            notebook_dir = argv[2]
        except ValueError:
            print('port value provided must be an integer')

    print('serving on port {0}'.format(port), file=stderr)
    httpd = HTTPServer(('0.0.0.0', port), GitStoreHandler)
    httpd.serve_forever()


if __name__ == '__main__':
    start_git_store()
