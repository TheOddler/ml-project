#!/usr/bin/env python3
# encoding: utf-8
"""
urlStreamHandler.py
"""

import sys
import argparse
import json
import http.server
import socketserver
import datetime
import atexit
import signal
import glob

from Guesser import Guesser

date = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
filename = "urls_{}.csv".format(date)
logfile = open(filename, "w")
print('Writing to {}'.format(filename))

guesser = Guesser()

def at_exit():
    print("Closing logfile")
    logfile.close()
atexit.register(at_exit)

def do_exit(sig, frame):
    print("\nShutting down")
    sys.exit(0)
signal.signal(signal.SIGINT, do_exit)

class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        """The GreaseMonkey script sends json data containing the url,
        timestamp, and html. We capture all POST requests irrespective of the
        path.
        """
        length = int(self.headers['Content-Length'])
        content = self.rfile.read(length)
        data = json.loads(content.decode(encoding='UTF-8'))
        url = data['url']
        ts = data['ts'] #timestamp
        action = data['action']
        if action == 'load':
            toppage = data['top']
            html = data['html']
            if toppage:
                action_str = 'load'
            else:
                action_str = 'bg'
            target = ''
            print('{:<15}: {}'.format(action_str, url))
        elif 'target' in data:
            action_str = action
            target = data['target']
            print('{:<15}: {} -> {}'.format(action_str, url, target))
        else:
            action_str = action
            target = ''
            print('{:<15}: {}'.format(action_str, url))
        logtext = '"'+ts+'", "'+action_str+'", "'+url+'", "'+target+'"'
        print(logtext, file=logfile)
        logfile.flush()
        
        # TODO: Call your model to learn from url and build up a list of next guesses
        guesser.learn(logtext)
        guesses = guesser.get_guesses(url)
        response = {
            'success': True,
            'guesses': guesses
        }
        jsonstr = bytes(json.dumps(response), "UTF-8")
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-length", len(jsonstr))
        self.end_headers()
        self.wfile.write(jsonstr)


def start_from_csv(filenames):
    """List of csv files that contain a url stream as if they were comming
    from the GreaseMonkey script."""
    guesser.learn_from_files(filenames)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Record and suggest urls')
    parser.add_argument('--verbose', '-v', action='count',
                        help='Verbose output')
    parser.add_argument('--port', '-p', default=8000,
                        help='Server port')
    parser.add_argument('--csv', nargs='*',
                        help='CSV files with a url stream to start from')
    args = parser.parse_args(argv)

    #all_csvs = glob.glob('./data/Our own/*.csv')
    all_csvs = glob.glob('./data/test/*.csv')
    #all_csvs = glob.glob('./data/*.csv')
    if args.csv is not None:
        all_csvs = all_csvs + args.csv
    if all_csvs is not None:
        start_from_csv(all_csvs)

    server = socketserver.TCPServer(("", args.port), MyRequestHandler)
    print("Serving at port {}".format(args.port))
    print("CTRL-C to exit")
    server.serve_forever()


if __name__ == "__main__":
    sys.exit(main())

