"""
Unit tests don't take arguments. Sometimes we like to pass an arg or two, e.g. you want to write test results to a file when running locally. This is a way to do that.

Setup:
 - add a directory `_test_config/` with a file `test.json` add config there in the form of json -- the top level key should the be same name as the unittest file, params in the dict val
 - add a dir `_test-results` to receive output.

 By default, these dirs are untracked in the riksdagen corpus repo (leading underscore).

 This is a mini module for repetitive functions related to this strategy for passing params to unittests.
"""
import inspect, json, os

def caller():
    for frame in inspect.stack()[1:]:
        if frame.filename[0] != '<':
            print(os.path.dirname(os.path.relpath(frame.filename)))
            break

def fetch_config(test):
    caller()
    try:
        with open("test/_test_config/test.json", 'r') as j:
            d = json.load(j)
            config = d[test]
            config['test_out_path'] = d['test_out_path']
        return config
    except:
        return None
