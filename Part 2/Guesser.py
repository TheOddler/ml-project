import sys
import argparse
import json
import http.server
import socketserver
import datetime
import atexit
import signal
import glob
import datetime
import numpy as np

class Guesser:

    def __init__(self):
        self.click_matrix = np.matrix([])

    def learn_from_files(self, filenames):
        for filename in filenames:
            with open(filename, 'r') as csv_file:
                # Incrementally train your model based on these files
                print('Processing {}'.format(filename))
                for line in csv_file:
                    self.learn(line)

    def learn(self, text):
        info = self.parse_log_line(text)
        print("Learning from: {}".format(info))

    def get_guesses(self, url):
        return [['https://dtai.cs.kuleuven.be/events/leuveninc-visionary-seminar-machine-learning-smarter-world', 0.9],
                ['link2_todo', 0.5]]

    def parse_log_line(self, text):
        try:
            words = [w.strip().strip('"') for w in text.split(',')]
            words[0] = datetime.datetime.strptime(words[0], "%Y-%m-%dT%H:%M:%S.%fZ")
            return {
                    'time': words[0],
                    'type': words[1],
                    'url': words[2],
                    'url2': words[3]
                }
        except:
            return None
