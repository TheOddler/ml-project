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
from itertools import count

class Guesser:

    def __init__(self):
        self.known_urls = [""] #to catch empty second url for "load" for example
        self.click_matrix = np.matrix([[0.0]]).copy()
        self.spend_time = [0.0]
        
        self.time_dictionary = {}

    def learn_from_files(self, filenames):
        for filename in filenames:
            with open(filename, 'r') as csv_file:
                # Incrementally train your model based on these files
                print('Processing {}'.format(filename))
                for line in csv_file:
                    self.learn(line)
        print('Learned info:')
        print('urls: {}'.format(self.known_urls))
        print('matrix:\n{}'.format(self.click_matrix))
        print('times: {}'.format(self.spend_time))
        print('size: {}'.format(len(self.known_urls)))
    
    def extend_data_to_include(self, url, url2):
        index_1, index_2 = self.get_indexes(url, url2)
        missing = index_1 < 0 or index_2 < 0
        if missing:
            none_index = self.get_index(None)
            if none_index >= len(self.known_urls) - 2:
                self.known_urls = self.known_urls + [None]*500 #extend per 500 for performance
            if index_1 < 0:
                self.known_urls[none_index] = url
                none_index += 1
            if index_2 < 0:
                self.known_urls[none_index]  = url2
                none_index += 1
            size = len(self.known_urls)
            
            padding = size - self.click_matrix.shape[0]     
            self.click_matrix = np.matrix(np.pad(self.click_matrix, pad_width=([0,padding], [0,padding]), mode='constant'))
            
            padding = size - len(self.spend_time)
            self.spend_time = np.pad(self.spend_time, pad_width=(0, padding), mode='constant')

    def learn(self, text):
        ## some checks
        assert (self.click_matrix.shape[0] == self.click_matrix.shape[1]), "Something wrong with the dimentions of the click matrix!"
        assert (self.click_matrix.shape[0] == len(self.known_urls)), "Something wrong with the number of known urls!"
        assert (len(self.spend_time) == len(self.known_urls)), "Time/url mismatch: {}-{}".format(len(self.spend_time), len(self.known_urls))
        
        info = self.parse_log_line(text)
        if info != None:
            self.extend_data_to_include(info.url, info.url2)
            
            #print("Learning {} from {} to {} at {}".format(info.type, info.url, info.url2, info.time))
        
            if info.type == "click":
                self.learn_click(info)
            elif info.type == "load":
                self.learn_load_unload(info)
            elif info.type == "beforeunload":
                self.learn_load_unload(info)
    
    def learn_load_unload(self, info):
        #print("learn_load_unload {}: {}".format(info.type, info.url))
        if info.type == "load":
            self.time_dictionary[info.url] = info.time
            #print("Load: {}".format(info.url))
        elif info.type == "beforeunload":
            if info.url in self.time_dictionary:
                delta_t = info.time - self.time_dictionary[info.url]
                del self.time_dictionary[info.url]
                index = self.get_index(info.url)
                self.spend_time[index] += delta_t.total_seconds()
                #print("known unload: {}".format(info.url))
            #else: #ignore
                #print("unknown unload: {}".format(info.url))
                
    
    def learn_click(self, info):
        assert (info.type == "click"), "Trying to learn from something non-clicky"
        fro = info.url #from is a keyword, so fro will have to do
        to = info.url2
        index_fro, index_to = self.get_indexes(fro, to)
        
        percentage = self.click_matrix[index_fro, index_to]
        percentage += 0.2
        self.click_matrix[index_fro, index_to] = percentage
        
        #print("Found {} to {}: {} -> {} \n {}".format(index_fro, index_to, fro, to, self.click_matrix))
        
        row_sum = self.click_matrix[index_fro,:].sum()
        self.click_matrix[index_fro,:] = self.click_matrix[index_fro,:] / row_sum
            
    def get_indexes(self, fro, to):
        return self.get_index(fro), self.get_index(to)
        
    def get_index(self, url):
        try: return self.known_urls.index(url)
        except: return -1

    def get_guesses(self, url):
        
        multi_matrix = self.click_matrix.copy()
        total_matrix = multi_matrix
        for i in range(10-1): # range of X gives X+1 steps
            multi_matrix = multi_matrix * self.click_matrix
            total_matrix += multi_matrix
        
        index = self.get_index(url)
        unordered_weights = total_matrix[index,:].getA1()
        weights, __, urls = zip(*sorted(zip(unordered_weights, count(), self.known_urls), reverse=True))
        
        #print(perc)
        #print(urls)
        print("Guessing for ({}) {}".format(index, url))
        
        url_limit = min(10, len(urls))
        result = []
        for i in range(url_limit):
            if weights[i] > 0:
                result.append([urls[i], weights[i]])
        
        if len(result) is 0:
            result = [["Can't guess :(", 0]]
        
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
