# HOW TO USE
#
# TODO test this script
#from gamcho import ipy; import IPython; IPython.embed(colors='neutral')
from pathlib import Path
import sys
from functools import cmp_to_key


def Dir(arg, path=Path.home() / 'buffer'):
    dir_list = dir(arg)
    public_api_list = []
    for api_name in dir_list:
        if api_name.startswith('_'):
            continue

        try:
            value = getattr(arg, api_name)
        except Exception as e:
            value = f"Exception thrown: '{e}'"

        public_api_list.append({
            'name': api_name,
            'value': value,
        })

    def compare_api(lhs, rhs):
        if callable(lhs['value']) and callable(rhs['value']):
            return -1 if lhs['name'] < rhs['name'] else +1

        if callable(rhs['value']):
            assert not callable(lhs['value'])
            return +1

        if callable(lhs['value']):
            assert not callable(rhs['value'])
            return -1

        assert not callable(lhs['value'])
        assert not callable(rhs['value'])
        return -1 if lhs['name'] < rhs['name'] else +1

    api_sort_key = cmp_to_key(compare_api)
    public_api_list.sort(key=api_sort_key)

    max_name_length = max([len(api['name']) for api in public_api_list])

    with open(path, 'w') as dump_file:
        for stream in [sys.stdout, dump_file]:
            print(f"Public API for {type(arg)}:", file=stream)
            for api_info in public_api_list:
                # yapf: disable
                print(
                    "{name:>{name_size}} | {value}".format(
                        name=api_info['name'],
                        name_size=max_name_length,
                        value=str(api_info['value']).partition('\n')[0]
                    ),
                    file=stream
                )
                # yapf: enable


def Help(arg, path=Path.home() / 'buffer'):
    with open(path, 'w') as dump_file:
        sys.stdout = dump_file
        help(arg)
        sys.stdout = sys.__stdout__
