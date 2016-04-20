# encoding: utf-8

import sys
import glob

from Util import Util
from Guesser import Guesser

def main(argv=None):
    print("Starting tests...")
    
    do_per_user_test()
    
    print("Done doing tests.")
    
def do_per_user_test():
    filepaths = find_all_csv_names()[:20] # [:20] for faster debugging
    
    # groups files with their user
    filepaths_per_user = {}
    for filepath in filepaths:
        file_id = filepath.rsplit("u",1)[-1].split(".",1)[0]
        [user_number, file_number] = file_id.split("_")
        
        if user_number in filepaths_per_user:
            filepaths_per_user[user_number].append(filepath)
        else:
            filepaths_per_user[user_number] = [filepath]
    
    #print("Files per user: {}".format(filepaths_per_user))
    
    # create test sets, one user is test, the others are the learning set
    test_sets = []
    for user, files in filepaths_per_user.items():
        test_set = {}
        test_set['test'] = files
        #[item for sublist in l for item in sublist]
        test_set['learn'] = [other_files for other_user, other_files in filepaths_per_user.items() if other_user != user]
        test_set['learn'] = [x for y in test_set['learn'] for x in y]
        test_set['user'] = user
        test_sets.append(test_set)
    
    #print("Test sets: {}".format(test_sets))
    
    Guesser.max_number_of_guesses = 5
    Guesser.use_derived_urls = True
    
    total_correct_guesses = 0
    total_missed_guesses = 0
    for test_set in test_sets:
        print("User Testing for: {}".format(test_set['user']))
        
        guesser = Guesser()
        guesser.learn_from_files(test_set['learn'])
        # do some guessing
        correct_guesses = 0
        missed_guesses = 0
        for log_file in test_set['test']:
            tester_log_file = TesterLogFile(log_file, use_derivatives = False)
            for idx, url in enumerate(tester_log_file.load_urls[:-1]):
                info_pairs = guesser.get_guesses(url)
                guessed_urls = [url for [url, weight] in info_pairs]
                if tester_log_file.contains_urls_for_guesses(guessed_urls, url, idx):
                    correct_guesses += 1
                else:
                    missed_guesses += 1
        total_correct_guesses += correct_guesses
        total_missed_guesses += missed_guesses
        print("{} correct guesses, {} missed guesses.".format(correct_guesses, missed_guesses))
        print()
        print()
    print("{} total correct guesses, {} total missed guesses".format(total_correct_guesses, total_missed_guesses))
    
    # test
    ## guess some stuff
    ## calculate accuracy

def find_all_csv_names():
    #all_csvs = glob.glob('./data/Our own/*.csv')
    #all_csvs = glob.glob('./data/test/*.csv')
    all_csvs = glob.glob('./data/*.csv') #user-testing assumes datafiles with "/.../uXX_XX.csv" format
    return all_csvs

class TesterLogFile:
    
    def __init__(self, filepath, use_derivatives = True):
        parsed_lines = []
        with open(filepath, 'r') as lines:
            parsed_lines = [Util.parse_log_line(line) for line in lines]
        parsed_lines = [info for info in parsed_lines if info is not None]
        # get load urls as these are the ones we'll be testing on
        self.load_urls = [info.url for info in parsed_lines if info.type == "load"]
        self.use_derivatives = use_derivatives
        #print(Load urls from {}: {}".format(filepath, self.load_urls))
    
    def contains_urls_for_guesses(self, guesses, guessing_for_url, guessing_index = -1):
        '''
        guesses: a list of guesses
        guessing_for_url: the url we're guessing for
        guessing_index: the index of the url, if it's one from this log file, otherwise -1
        '''
        other_urls = self.load_urls.copy()
        if guessing_index > 0:
            other_urls = other_urls[guessing_index+1:]
        
        if self.use_derivatives:
            # add derivatives
           other_urls = [[url]+Util.get_derived_urls(url) for url in other_urls]
           other_urls = [x for y in other_urls for x in y] #flatten
        # find intersection
        intersection = [i for i in guesses if i in other_urls]
        #print("Guessed urls: {}, with intersection: {}".format(urls, intersection))
        return len(intersection) > 0

if __name__ == "__main__":
    sys.exit(main())
