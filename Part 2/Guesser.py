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
        self.known_urls = []
        self.click_matrix = np.matrix([0.0]).copy()

    def learn_from_files(self, filenames):
        for filename in filenames:
            with open(filename, 'r') as csv_file:
                # Incrementally train your model based on these files
                print('Processing {}'.format(filename))
                for line in csv_file:
                    self.learn(line)
        print('Learned info:')
        print('urls: {}'.format(self.known_urls))
        print(self.click_matrix)

    def learn(self, text):
        info = self.parse_log_line(text)
        #print("Learning from: {}".format(info))
        if info != None and info.type == "click":
            fro = info.url #from is a keyword, so fro will have to do
            to = info.url2
            index_fro, index_to = self.get_indexes(fro, to)
            if index_fro < 0:
                self.known_urls.append(fro)
                index_fro = len(self.known_urls)-1
            if index_to < 0:
                self.known_urls.append(to)
                index_to = len(self.known_urls)-1
            size = len(self.known_urls)
            self.click_matrix.resize(size, size)
            
            #print("{},{}".format(self.click_matrix.shape, size))
            
            percentage = self.click_matrix.item(index_fro, index_to)
            percentage += 0.2
            self.click_matrix[index_fro, index_to] = percentage
            if percentage > 1:
                print("New count {} from {} to {}".format(percentage, info.url, info.url2))
            
            row_sum = self.click_matrix[index_fro,:].sum()
            self.click_matrix[index_fro,:] = self.click_matrix[index_fro,:] / row_sum
            
    def get_indexes(self, fro, to):
        return self.get_index(fro), self.get_index(to)
        
    def get_index(self, url):
        try: return self.known_urls.index(url)
        except: return -1

    def get_guesses(self, url):
        index = self.get_index(url)
        unordered_perc = self.click_matrix[index,0:].getA1()
        perc, urls = zip(*sorted(zip(unordered_perc, self.known_urls), reverse=True))
        
        #print(perc)
        #print(urls)
        
        count = min(10, len(urls))
        result = []
        for i in range(count):
            if perc[i] > 0:
                result.append([urls[i], perc[i]])
        
        return result

    def parse_log_line(self, text):
        try:
            words = [w.strip().strip('"') for w in text.split(',')]
            words[0] = datetime.datetime.strptime(words[0], "%Y-%m-%dT%H:%M:%S.%fZ")
            return type('',(object,),{
                    'time': words[0],
                    'type': words[1],
                    'url': words[2],
                    'url2': words[3]
                })()
        except:
            return None
