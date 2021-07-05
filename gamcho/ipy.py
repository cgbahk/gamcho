# HOW TO USE
#
# TODO test this script
#from gamcho import ipy; import IPython; IPython.embed(colors='neutral')
from pathlib import Path
import pprint as pp
import sys


def Dir(arg, path=Path.home() / 'buffer'):
    dir_list = dir(arg)
    public_api_list = [elem for elem in dir_list if not elem.startswith('_')]
    with open(path, 'w') as dump_file:
        for stream in [sys.stdout, dump_file]:
            print(f"Public API for {type(arg)}:", file=stream)
            pp.pprint(public_api_list, stream=stream)


def Help(arg, path=Path.home() / 'buffer'):
    with open(path, 'w') as dump_file:
        sys.stdout = dump_file
        help(arg)
        sys.stdout = sys.__stdout__
