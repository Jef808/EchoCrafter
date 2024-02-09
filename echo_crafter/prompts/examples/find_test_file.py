#!/usr/bin/env python

import os
import sys

def find_test_file(filepath):
    test_filenames = [os.path.basename(filepath).replace('.tsx', '.test.js')]
    possible_paths = [os.path.join(os.path.dirname(filepath), name) for name in test_filenames]
    possible_paths.append(os.path.join(os.path.dirname(filepath), 'tests', test_filenames[0]))

    test_file = 'NOT FOUND'
    for path in possible_paths:
        if os.path.isfile(path):
            test_file = path
            break

    print(test_file)


if __name__ == '__main__':
    filepath = sys.argv[1]
    if not os.path.isabs(filepath):
        filepath = os.path.abspath(filepath)
    find_test_file(filepath)
