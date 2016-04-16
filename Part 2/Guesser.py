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
        self.known_urls = [""]
        self.click_matrix = np.matrix([[0.0]]).copy()

    # aangepast niet op volgerde maar op 
    # open die file check de eerste lijn
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
        ## some checks
        assert (self.click_matrix.shape[0] == self.click_matrix.shape[1]), "Something wrong with the dimentions of the click matrix!"
        assert (self.click_matrix.shape[0] == len(self.known_urls)), "Something wrong with the number of known urls!"
        
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
            padding = size - self.click_matrix.shape[0]     
            
            self.click_matrix = np.matrix(np.pad(self.click_matrix, pad_width=([0,padding], [0,padding]), mode='constant'))
            
            percentage = self.click_matrix[index_fro, index_to]
            percentage += 0.2
            self.click_matrix[index_fro, index_to] = percentage
            
            #print("Found {} to {}: {} -> {} \n {}".format(index_fro, index_to, fro, to, self.click_matrix))
            
            #normalize the row
            row_sum = self.click_matrix[index_fro,:].sum() #moet altijd 1,2 zijn behalve in begin 0,2
            self.click_matrix[index_fro,:] = self.click_matrix[index_fro,:] / row_sum
            
    def get_indexes(self, fro, to):
        return self.get_index(fro), self.get_index(to)
        
    def get_index(self, url):
        try: return self.known_urls.index(url)
        except: return -1

    def get_guesses(self, url):
        
        # klik matrix enkel eerste stap
        # multi matrix is kans na multi stappen op bepaalde link belandt
        # bereken dat is 10 stapjes
        # tel al die boel op = total matrix
        # het zijn allemaal gewichten -> niet genormaliseerd
        # normaliseren is niet meer nodig
        # ze verwachten niet per se dat dat echt kansen zijn
        # total matrix wat is de kans dt ik in 1 stap bij r/nintendo zit, binnen 2 stappen, 3 stappen, etc...
        multi_matrix = self.click_matrix.copy()
        total_matrix = multi_matrix
        for i in range(10-1): # range of X gives X+1 steps
            multi_matrix = multi_matrix * self.click_matrix
            total_matrix += multi_matrix
        
        # neem de huidige url
        index = self.get_index(url)
        # neem de rij van de huidige url
        # gewichtjes van al de mogelijke urls
        # sorteer die
        # zie de url die de meeste kans heeft om de volgende te zijn
        unordered_perc = total_matrix[index,:].getA1()
        # sorteer op die gewichtjes
        # known_urls list wordt in sync gehouden
        # sorteer die tezamen gebaseerd op unordered_weigths
        # reverse=true -> grootste eerst
        perc, urls = zip(*sorted(zip(unordered_perc, self.known_urls), reverse=True))
        
        #debug info
        #print(perc)
        #print(urls)
        print("Guessing for ({}) {}".format(index, url))
        
        # de tien gokken met de hoogste waarde
        # return de tien hoogste 
        # als er minder dan tien zijn, print die dan
        # als er urls zijn met waarde0 die worden dan genegeerd
        count = min(10, len(urls))
        result = []
        for i in range(count):
            if perc[i] > 0:
                result.append([urls[i], perc[i]])
        # als niets kan gokken, toon sad :(
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
            
            #learn from files
