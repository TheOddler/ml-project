import sys
import argparse
import json
import http.server
import socketserver
import datetime
import atexit
import signal
import glob

class Guesser:

    def __init__(self):
        print('Creating guesser')

    def learn_from_files(self, filenames):
        for filename in filenames:
            with open(filename, 'r') as csv_file:
                # TODO: Incrementally train your model based on these files
                print('Processing {}'.format(filename))

    def learn(self, text):
        print("Learning from: {}".format(text))

    def get_guesses(self, url):
        return [['https://dtai.cs.kuleuven.be/events/leuveninc-visionary-seminar-machine-learning-smarter-world', 0.9],
                ['link2_todo', 0.5]]
