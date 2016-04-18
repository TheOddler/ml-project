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
        test_sets.append(test_set)
    
    #print("Test sets: {}".format(test_sets))
    
    for test_set in test_sets:
        print("User Testing for: {}".format(test_set))
        
        guesser = Guesser()
        guesser.learn_from_files(test_set['learn'])
        # do some guessing
        total_correct_guesses = 0        
        for log_file in test_set['test']:
            tester_log_file = TesterLogFile(log_file)
            for info in tester_log_file.parsed_lines:
                if info.type == "load":
                    if tester_log_file.contains_guesses_from_for(guesser, info.url):
                        total_correct_guesses += 1
        print("Total correct guesses: {}".format(total_correct_guesses))
        print()
        print()
        
    # test
    ## guess some stuff
    ## calculate accuracy

def find_all_csv_names():
    #all_csvs = glob.glob('./data/Our own/*.csv')
    #all_csvs = glob.glob('./data/test/*.csv')
    all_csvs = glob.glob('./data/*.csv')
    return all_csvs

class TesterLogFile:
    
    def __init__(self, filepath):
        self.parsed_lines = []
        with open(filepath, 'r') as lines:
            self.parsed_lines = [Util.parse_log_line(line) for line in lines]
        self.parsed_lines = [info for info in self.parsed_lines if info is not None]
    
    def contains_guesses_from_for(self, guesser, for_url):
        return True

if __name__ == "__main__":
    sys.exit(main())
