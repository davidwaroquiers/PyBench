__author__ = 'setten'

from PyBench.core.descriptions import get_description
from PyBench.core.benchmarks import get_benchmark

if __name__ == "__main__":
    code = 'vasp'
    desc = get_description(code=code)
    desc.print_template()
    bench = get_benchmark(code=code)
    bench.create_input()