"""Run all tests associated with this package.

Run by executing Python3 run_all_tests.py (do not use -m)
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import unittest  # noqa: E402

if __name__ == '__main__':
    test_suite = unittest.defaultTestLoader.discover('./', 'test_*.py')
    test_runner = unittest.TextTestRunner(resultclass=unittest.TextTestResult)
    result = test_runner.run(test_suite)
    # specify an exit code for integrations with CI(hound,travis,etc)
    sys.exit(not result.wasSuccessful())
