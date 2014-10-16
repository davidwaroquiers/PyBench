from __future__ import print_function, division

__author__ = 'setten'
__version__ = "0.1"
__maintainer__ = "Michiel van Setten"
__email__ = "mjvansetten@gmail.com"
__date__ = "Sept 2014"


"""
Script to setup a set of benchmark calculations
"""


from PyBench.core.descriptions import get_description
from PyBench.core.benchmarks import get_benchmark
import os

if __name__ == "__main__":
    code = 'vasp'
    desc = get_description(code=code)
    if not os.path.isfile('description'):
        desc.print_template()
    bench = get_benchmark('standard_vasp', code=code)
    bench.create_input()
    bench.create_job_collection()