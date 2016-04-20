# encoding: utf-8

import numpy as np
import logging

from Util import Util

class Guesser:
    
    # the guesser will return maximum this many guesses
    # it will gues anything with a >0 wieght, and guess the 10 with highest weight
    max_number_of_guesses = 10
    
    # When clicking on an url, how much does it percentage grow?
    # It's current percantage is increased with this, and then everything is normalized again
    url_click_percentage_increase = 0.2
    
    # time-spend others multiplyer
    # Whenever a new time-spend is added, all others are multiplied with this, thus giving more weigt to recent activity
    # 1 just means everything will be the total time spend on that page
    # look out with this, don't make it too small (0.9 is small already I think)
    time_spend_others_multiplyer = 1
    
    # To prevent time outliers I use a robust fitter function:
    # time^2/(width^2 + time^2)
    use_robust_time = True #otherwise it's just total time
    time_width = 60.0 #at time_width seconds it will have half the scale, at twice this it will be about the scale
    # that robust fitter function is scaled with this
    time_scale = 120.0
    # if this is double of the width, it will closely resemply linear but slower at the start, and top off at time_scale
    # look at: https://www.google.com/search?q=time^2%2F%28width^2+%2B+time^2%29&ie=utf-8&oe=utf-8#q=120*%28x^2%2F%2860^2+%2B+x^2%29%29%2C+x
    
    # How many steps the algorithm look in the click matrix
    number_of_click_steps = 5
    # when calculating the next N-next step change, this is scaled with this fallout to the N'th power
    multi_step_falloff = 0.9
    
    # Whether or not to learn with derived urls
    use_derived_urls = True
    # urls are derived, the considered time is multiplied by this fallout to the poewr of the derivation
    derived_time_falloff = 0.8 #1 means no falloff, 0 is the same as disabling this
    # similar to the time falloff, but for the click percentage increase
    derived_click_falloff = 0.8 #1 means no falloff, 0 is the same as disabling this
    # how much do the guesses for derived urls count in the final guess, similar use of power of the derivation
    devied_guess_falloff = 0.7 #1 means no falloff, 0 is the same as disabling this

    def __init__(self):
        self.known_urls = [""] #to catch empty second url for "load" for example
        self.click_matrix = np.matrix([[0.0]]).copy()
        self.spend_time = [0.0]
        
        self.time_dictionary = {}
        self.guesses_click_matrix = None

    # aangepast niet op volgerde maar op 
    # open die file check de eerste lijn
    def learn_from_files(self, filenames):
        file_times = []
        proper_file_names = []
        removed_file_names = []
        for filename in filenames:
            with open(filename, 'r') as csv_file:
                info = None
                for line in csv_file:
                    info = Util.parse_log_line(line)
                    if info is not None:
                        break
                if info is not None:
                    file_times.append(info.time)
                    proper_file_names.append(filename)
                else:
                    removed_file_names.append(filename)
        
        file_times, proper_file_names = zip(*sorted(zip(file_times, proper_file_names), key=lambda x: x[0]))
        
        logging.debug("Removed files (empty or crap): {}".format(removed_file_names))
        for i in range(len(proper_file_names)):
            filename = proper_file_names[i]
            filetime = file_times[i]
            with open(filename, 'r') as csv_file:
                # Incrementally train your model based on these files
                logging.debug('Processing ({}) -> {}'.format(filetime, filename))
                for line in csv_file:
                    self.learn(line)
        logging.debug('Learned info:')
        #logging.debug('urls (first 100): {}...'.format(self.known_urls[0:100]))
        #logging.debug('matrix:\n{}'.format(self.click_matrix))
        #logging.debug('times (first 100): {}'.format(self.spend_time[0:100]))
        logging.debug('size: {}'.format(sum(x is not None for x in self.known_urls)))

    def learn(self, text):
        ## some checks
        assert (self.click_matrix.shape[0] == self.click_matrix.shape[1]), "Something wrong with the dimentions of the click matrix!"
        assert (self.click_matrix.shape[0] == len(self.known_urls)), "Something wrong with the number of known urls!"
        assert (len(self.spend_time) == len(self.known_urls)), "Time/url mismatch: {}-{}".format(len(self.spend_time), len(self.known_urls))
        
        info = Util.parse_log_line(text)
        if info != None:
            if Guesser.use_derived_urls:
                all_urls = [info.url]
                all_urls.extend(Util.get_derived_urls(info.url))
                all_urls2 = [info.url2]
                all_urls2.extend(Util.get_derived_urls(info.url2))
                
                for idx, url in enumerate(reversed(all_urls)):
                    for idx2, url2 in enumerate(reversed(all_urls2)):
                        info.url = url
                        info.url2 = url2
                        self.learn_info(info, idx + idx2)
            else:
                self.learn_info(info)
            
    
    def learn_info(self, info, derived = 0):
        assert (info is not None), "Learning from None :s"
        self.extend_data_to_include(info.url, info.url2)
        
        if info.type == "click":
            self.learn_click(info, derived)
        elif info.type == "load":
            self.learn_load_unload(info, derived)
        elif info.type == "beforeunload":
            self.learn_load_unload(info, derived)
    
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
    
    def learn_load_unload(self, info, derived):
        if info.type == "load":
            self.time_dictionary[info.url] = info.time
        elif info.type == "beforeunload":
            if info.url in self.time_dictionary:
                delta_t = info.time - self.time_dictionary[info.url]
                del self.time_dictionary[info.url]
                index = self.get_index(info.url)
                self.spend_time *= Guesser.time_spend_others_multiplyer
                self.spend_time[index] += delta_t.total_seconds() * (Guesser.derived_time_falloff ** derived)
                
    
    def learn_click(self, info, derived):
        assert (info.type == "click"), "Trying to learn from something non-clicky"
        self.guesses_click_matrix = None        
        
        fro = info.url #from is a keyword, so fro will have to do
        to = info.url2
        index_fro, index_to = self.get_indexes(fro, to)
        
        percentage = self.click_matrix[index_fro, index_to]
        percentage += Guesser.url_click_percentage_increase * (Guesser.derived_click_falloff ** derived)
        self.click_matrix[index_fro, index_to] = percentage
        
        row_sum = self.click_matrix[index_fro,:].sum()
        self.click_matrix[index_fro,:] = self.click_matrix[index_fro,:] / row_sum
        
    def get_indexes(self, fro, to):
        return self.get_index(fro), self.get_index(to)
        
    def get_index(self, url):
        try: return self.known_urls.index(url)
        except: return -1

    def get_guesses(self, url):
        url = Util.clean_url(url)
        
        # this fills self.guesses_matrix
        if self.guesses_click_matrix is None:
            self.calculate_guesses_click_matrix()
        
        # neem de huidige url
        index = self.get_index(url)
        unordered_weights = self.guesses_click_matrix[index,:].getA1()
        if Guesser.use_derived_urls:
            for idx, derived_url in enumerate(Util.get_derived_urls(url), start=1):
                der_index = self.get_index(derived_url)
                der_weights = self.guesses_click_matrix[der_index,:].getA1()
                unordered_weights = [w + dw * (Guesser.devied_guess_falloff ** idx) for w,dw in zip(unordered_weights, der_weights)]
        
        # add time knowledge
        unordered_weights = [w * self.make_time_robust(t) for w,t in zip(unordered_weights, self.spend_time)]
        weights, urls = zip(*sorted(zip(unordered_weights, self.known_urls), reverse=True, key=lambda x: x[0]))
        
        #debug info
        logging.debug("Guessed for ({}) {}".format(index, url))
        

        url_limit = min(Guesser.max_number_of_guesses, len(urls))
        result = []
        for i in range(url_limit):
            if weights[i] > 0:
                result.append([urls[i], weights[i]])
        
        if len(result) is 0:
            result = [["Can't guess :(", 0]]
        
        return result
    
    def calculate_guesses_click_matrix(self):
        logging.debug("Recalculating guesses click matrix...")
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
        for i in range(1, Guesser.number_of_click_steps): # range of X gives X+1 steps
            multi_matrix = multi_matrix * self.click_matrix
            total_matrix += (Guesser.multi_step_falloff**i) * multi_matrix
        self.guesses_click_matrix = total_matrix

    def make_time_robust(self, time):
        if Guesser.use_robust_time:
            return Guesser.time_scale * (time**2 / (Guesser.time_width**2 + time**2))
        else:
            return time

