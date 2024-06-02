# -*- coding: utf-8 -*-
"""Utility Classes and Functions

    @author: Liangjun Zhu

    @changlog:

     - 2024-06-02 - ljzhu - original version.
"""
import json
import uuid
from typing import Iterator


def load_jsonfile(jsonfile, encoding='utf-8'):
    with open(jsonfile, 'r', encoding=encoding) as f:
        metadata = json.load(f)
    return metadata


def save_jsonfile(jsondata, jsonfile):
    tmp = json.dumps(jsondata, indent=4)
    with open(jsonfile, 'w') as f:
        f.write('%s' % tmp)


def generate_uniqueid():
    # type: () -> Iterator[int]
    """Generate unique integer ID for Scenario using uuid.

    Usage:
        uniqueid = next(generate_uniqueid())
    """
    uid = int(str(uuid.uuid4().fields[-1])[:9])
    while True:
        yield uid
        uid += 1


if __name__ == '__main__':
    # Run doctest in docstrings of Google code style
    # python -m doctest utils.py (only when doctest.ELLIPSIS is not specified)
    # or python utils.py -v
    # or py.test --doctest-modules utils.py
    import doctest

    doctest.testmod()