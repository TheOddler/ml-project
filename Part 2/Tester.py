# encoding: utf-8

import sys
import glob
import itertools
from random import shuffle
import logging

from Util import Util
from Guesser import Guesser

use_file_subset_for_debugging = True

def main(argv=None):
    # prepare logger
    logging.basicConfig(level=logging.INFO) #set this to info to disable log clutter
    logging.getLogger().handlers = [logging.StreamHandler(), logging.FileHandler("guesser.log"), ]
    
    logging.info("Starting tests...")
    logging.info("---")
    
    # log to a file rather than the console
    #log_file = open("message.log","w")
    #sys.stdout = log_file    
    
    # these are overritten if you use "do_all_tests_with_settings"
    Guesser.max_number_of_guesses = 5
    Guesser.use_derived_urls = True
    TesterLogFile.use_derivatives = False
    
    #do_per_user_test()
    #do_random_cross_validation_test()
    #do_time_test()
    
    do_all_test_with_settings()
    
    logging.info("Done doing tests.")

def do_all_test_with_settings():
    # tests are run with all combinations of these, so look out since this can become a lot!
    list_of_max_number_of_guesses = [10]
    list_of_url_click_percentage_increase = [0.2]
    list_of_time_spend_others_multiplyer = [1]
    list_of_use_robust_time = [True]
    list_of_time_width = [60.0]
    list_of_time_scale = [120.0]
    list_of_number_of_click_steps = [5]
    list_of_multi_step_falloff = [0.9]
    
    list_of_use_derived_urls = [True, False]
    list_of_derived_time_falloff = [0.8]
    list_of_derived_click_falloff = [0.8]
    list_of_devied_guess_falloff = [0.7]
    
    list_of_log_file_use_derivatives = [True, False]
    
    for (max_number_of_guesses,
        url_click_percentage_increase,
        time_spend_others_multiplyer,
        use_robust_time,
        time_width,
        time_scale,
        number_of_click_steps,
        multi_step_falloff,
        
        use_derived_urls,
        derived_time_falloff,
        derived_click_falloff,
        devied_guess_falloff,
        
        log_file_use_derivatives) in itertools.product(list_of_max_number_of_guesses,
            list_of_url_click_percentage_increase,
            list_of_time_spend_others_multiplyer,
            list_of_use_robust_time,
            list_of_time_width,
            list_of_time_scale,
            list_of_number_of_click_steps,
            list_of_multi_step_falloff,
            
            list_of_use_derived_urls,
            list_of_derived_time_falloff,
            list_of_derived_click_falloff,
            list_of_devied_guess_falloff,
            
            list_of_log_file_use_derivatives):
        Guesser.max_number_of_guesses = max_number_of_guesses
        Guesser.url_click_percentage_increase = url_click_percentage_increase
        Guesser.time_spend_others_multiplyer = time_spend_others_multiplyer
        Guesser.use_robust_time = use_robust_time
        Guesser.time_width = time_width
        Guesser.time_scale = time_scale
        Guesser.number_of_click_steps = number_of_click_steps
        Guesser.multi_step_falloff = multi_step_falloff
        
        Guesser.use_derived_urls = use_derived_urls
        Guesser.derived_time_falloff = derived_time_falloff
        Guesser.derived_click_falloff = derived_click_falloff
        Guesser.devied_guess_falloff = devied_guess_falloff
        
        TesterLogFile.use_derivatives = log_file_use_derivatives
        
        logging.info("Doing all tests with settings: ")
        Util.print_class_vars_for(Guesser, "Guesser settings: {}")
        Util.print_class_vars_for(TesterLogFile, "TesterLogFile settings: {}")
        do_all_tests()
        logging.info("---")

def do_all_tests():
    do_per_user_test()
    do_random_cross_validation_test()
    do_time_test()
    
def do_per_user_test():
    filepaths = find_all_csv_names()
    
    # groups files with their user
    filepaths_per_user = {}
    for filepath in filepaths:
        file_id = filepath.rsplit("u",1)[-1].split(".",1)[0]
        [user_number, file_number] = file_id.split("_")
        
        if user_number in filepaths_per_user:
            filepaths_per_user[user_number].append(filepath)
        else:
            filepaths_per_user[user_number] = [filepath]
    
    # create test sets, one user is test, the others are the learning set
    test_sets = []
    for user, files in filepaths_per_user.items():
        test_set = {}
        test_set['test'] = files
        test_set['learn'] = [other_files for other_user, other_files in filepaths_per_user.items() if other_user != user]
        test_set['learn'] = [x for y in test_set['learn'] for x in y] #flatten
        test_set['id'] = "user-{}".format(user)
        test_sets.append(test_set)
    
    total_correct_guesses, total_missed_guesses, total_correct_count, total_missed_count = run_test_sets(test_sets)
    
    logging.info("-> User tests: {} total hits, {} total misses, {} total hit count, {} total miss count".format(total_correct_guesses, total_missed_guesses, total_correct_count, total_missed_count))

def do_random_cross_validation_test():
    filepaths = find_all_csv_names()
    
    #randomize the sessions/files
    shuffle(filepaths)
    #divide in 5 equal parts
    parts = [filepaths[i::5] for i in range(5)]
    
    # generate test_sets
    test_sets = []
    for idx, part in enumerate(parts):
        test_set = {}
        test_set['test'] = part
        test_set['learn'] = [other_part for other_part in parts if other_part is not part]
        test_set['learn'] = [x for y in test_set['learn'] for x in y] #flatten
        test_set['id'] = "cross-validation-part-{}".format(idx)
        test_sets.append(test_set)
    
    total_correct_guesses, total_missed_guesses, total_correct_count, total_missed_count = run_test_sets(test_sets)
    
    logging.info("-> Cross-validation tests: {} total hits, {} total misses, {} total hit count, {} total miss count".format(total_correct_guesses, total_missed_guesses, total_correct_count, total_missed_count))

def do_time_test():
    file_paths = find_all_csv_names()
    
    # sort by first log
    file_times = []
    proper_file_names = []
    removed_file_names = []
    for filename in file_paths:
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
    file_times, sorted_file_paths = zip(*sorted(zip(file_times, proper_file_names), key=lambda x: x[0]))
    
    number_of_files = len(sorted_file_paths)
    limiter = int(number_of_files / 5 * 4)
    last_part = sorted_file_paths[limiter:]
    first_part = sorted_file_paths[:limiter]
    
    test_set = {}
    test_set['test'] = last_part
    test_set['learn'] = first_part
    test_set['id'] = "time-test"
    
    total_correct_guesses, total_missed_guesses, total_correct_count, total_missed_count = run_test_set(test_set)
    
    logging.info("-> Time tests: {} total hits, {} total misses, {} total hit count, {} total miss count".format(total_correct_guesses, total_missed_guesses, total_correct_count, total_missed_count))

def run_test_sets(test_sets):
    '''
    test_sets = list of dict: {'learn', 'test', 'id'}
            'learn' is a list of files to learn from
            'test' is a list of files to test
            'id' is an id for this test-set
    '''
    total_correct_guesses = 0
    total_missed_guesses = 0
    total_correct_count = 0
    total_missed_count = 0
    for test_set in test_sets:
        correct_guesses, missed_guesses, correct_count, missed_count = run_test_set(test_set)
        total_correct_guesses += correct_guesses
        total_missed_guesses += missed_guesses
        total_correct_count += correct_count
        total_missed_count += missed_count
    return total_correct_guesses, total_missed_guesses, total_correct_count, total_missed_count

def run_test_set(test_set):
    '''
    test_set = dict: {'learn', 'test', 'id'}
            'learn' is a list of files to learn from
            'test' is a list of files to test
            'id' is an id for this test-set
    '''
    guesser = Guesser()
    guesser.learn_from_files(test_set['learn'])
    # do some guessing
    correct_guesses = 0
    missed_guesses = 0
    correct_count = 0
    missed_count = 0
    for log_file in test_set['test']:
        tester_log_file = TesterLogFile(log_file)
        for idx, url in enumerate(tester_log_file.load_urls[:-1]):
            info_pairs = guesser.get_guesses(url)
            guessed_urls = [url for [url, weight] in info_pairs]
            local_correct_count = tester_log_file.number_of_urls_for_guesses(guessed_urls, url, idx)
            local_missed_count = len(guessed_urls) - local_correct_count
            if local_correct_count > 0:
                correct_guesses += 1
            else:
                missed_guesses += 1
            correct_count += local_correct_count
            missed_count += local_missed_count
    logging.info("Tested set {}: {} hits, {} misses, {} hit count, {} miss count".format(test_set['id'], correct_guesses, missed_guesses, correct_count, missed_count))
    return correct_guesses, missed_guesses, correct_count, missed_count
    

def find_all_csv_names():
    #all_csvs = glob.glob('./data/Our own/*.csv')
    #all_csvs = glob.glob('./data/test/*.csv')
    all_csvs = glob.glob('./data/*.csv') #user-testing assumes datafiles with "/.../uXX_XX.csv" format
    if use_file_subset_for_debugging:
        all_csvs = all_csvs[:21] # [:20] for faster debugging
    return all_csvs

class TesterLogFile:
    
    use_derivatives = True
    
    def __init__(self, filepath):
        parsed_lines = []
        with open(filepath, 'r') as lines:
            parsed_lines = [Util.parse_log_line(line) for line in lines]
        parsed_lines = [info for info in parsed_lines if info is not None]
        # get load urls as these are the ones we'll be testing on
        self.load_urls = [info.url for info in parsed_lines if info.type == "load"]
    
    def number_of_urls_for_guesses(self, guesses, guessing_for_url, guessing_index = -1):
        '''
        guesses: a list of guesses
        guessing_for_url: the url we're guessing for
        guessing_index: the index of the url, if it's one from this log file, otherwise -1
        '''
        other_urls = self.load_urls.copy()
        if guessing_index > 0:
            other_urls = other_urls[guessing_index+1:]
        
        if TesterLogFile.use_derivatives:
            # add derivatives
           other_urls = [[url]+Util.get_derived_urls(url) for url in other_urls]
           other_urls = [x for y in other_urls for x in y] #flatten
        # find intersection
        intersection = [i for i in guesses if i in other_urls]
        return len(intersection)

if __name__ == "__main__":
    sys.exit(main())
