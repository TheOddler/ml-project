# -*- coding: utf-8 -*-

import datetime
import logging

class Util:
    
    @staticmethod
    def parse_log_line(text):
        try:
            words = [w.strip().strip('"') for w in text.split(',')]

            url = Util.clean_url(words[2])
            if url == "":
                return None
            else:
                time = datetime.datetime.strptime(words[0], "%Y-%m-%dT%H:%M:%S.%fZ")
                url2 = Util.clean_url(words[3])
                return type('',(object,),{
                        'time': time,
                        'type': words[1],
                        'url': url,
                        'url2': url2
                    })()
        except:
            return None
            
    @staticmethod
    def clean_url(url):
        url = url.strip()
        url = url.split("?", 1)[0]
        url = url.strip("/")
        return url
        
    @staticmethod
    def get_derived_urls(url):
        all = []                      
        der = Util.get_derived_url(url)
        while der is not None:
            all.append(der)
            der = Util.get_derived_url(der)
        return all
        
    @staticmethod
    def get_derived_url(url):
        split = url.rsplit('/', 1)
        if len(split) <= 1:
            return None
        elif split[0].endswith('/'):
            return None
        else:
            return split[0]
    
    @staticmethod
    def print_class_vars_for(clss, fomat_string = "{}"):
        class_vars = [(var, val) for (var, val) in clss.__dict__.items() if not hasattr(val, '__call__') and not var.startswith('__')]
        logging.info(fomat_string.format(class_vars))