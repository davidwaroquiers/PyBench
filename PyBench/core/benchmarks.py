from __future__ import print_function, division

__author__ = 'setten'
__version__ = "0.1"
__maintainer__ = "Michiel van Setten"
__email__ = "mjvansetten@gmail.com"
__date__ = "Sept 2014"

"""
PyBench is a package to automatically run a series of bechmarktests of an abinitio code
Benchmark describe a set of calculations in principle independent of a code
"""
import os
import copy
import sys
from pymatgen.matproj.rest import MPRester, MPRestError
from pymatgen.io.vaspio_set import MPStaticVaspInputSet
from pymatgen.transformations.standard_transformations import SupercellTransformation
from pymatgen.io.abinitio.tasks import TaskManager
from pymatgen.io.vaspio.vasp_input import Poscar

#def npar(parameter, n):
#    return int(n ** parameter)


def functions(function_type):
    """
    functions for generating input parameters that are a function of the ncpus
    benchmark.parameters_list provides a list of parameters that are looped over. The corresponding function
    provides the actual values
    """
    def npar(parameter, n):
        """function for NPAR"""
        return int(n ** parameter)
    l = {'NPAR': npar}
    return l[function_type]


class BenchVaspInputSet(MPStaticVaspInputSet):
        def get_poscar(self, structure):
            return Poscar(structure)

        def set_input(self):
            self.incar_settings = {'ENCUT': 300, 'PREC': 'Normal', 'NSW': 0, 'LWAVE': False, 'LREAL': 'AUTO'}


class Benchmark():
    """
    describing a benchmark
    """
    def __init__(self, code='vasp', system_id='mp-149', **kwargs):
        """
        system_id is to be a mp-id to take a base structure from the mp-database
        kwarg can be used to personalize all lists

        code specifies the name of the code to be tested, it is assumed that an executable with this name is
        present in the current work dir

        to generate the job scripts a taskmanager.yml file is needed in the current work dir
        #todo add example

        list of paralelizaions
        """
        self.code = code
        self.subject = os.path.join(os.getcwd(), code)
        self.manager = TaskManager.from_user_config()
        self.script_list = []
        self.system_id = system_id
        mp_key = os.environ['MP_KEY']
        with MPRester(mp_key) as mp_database:
            self.structure = mp_database.get_structure_by_material_id(system_id, final=True)
        self.name = str(self.structure.composition.reduced_formula) + "_" + str(self.system_id)
        self.np_list = [1, 2, 4, 16, 32, 64, 128]
        self.sizes = [1, 2, 3]
        self.parameter_lists = None
        if self.code == 'vasp':
            self.parameter_lists = {'NPAR': [0, 0.5, 1]}
        xx = 0
        for parameter in self.parameter_lists:
            xx += len(self.parameter_lists[parameter])
        self.total = len(self.np_list)*len(self.sizes)*xx
        self.bar_len = len(self.sizes) + 1 + self.total

    def create_input(self):
        """
        create input for all the benchmark calculations

        :return 0 on succes
        """
        inpset = BenchVaspInputSet()
        inpset.set_input()
        print('testing executable %s' % self.subject)
        print("creating input for %s system sizes and %s calculations per size:" %
              (len(self.sizes), int(self.total / len(self.sizes))))
        sys.stdout.write(self.bar_len*"-"+"\n")
        sys.stdout.flush()
        for s in self.sizes:
            print('size', s)
            sys.stdout.write("|")
            sys.stdout.flush()
            struc = copy.deepcopy(self.structure)
            trans = SupercellTransformation.from_scaling_factors(scale_a=s, scale_b=s, scale_c=s)
            struc = trans.apply_transformation(struc)
            for n in self.np_list:
                print(n)
                for x in self.parameter_lists:
                    print(x)
                    for o in self.parameter_lists[x]:
                        print(o)
                        sys.stdout.write("*")
                        sys.stdout.flush()
                        v = functions(x)(o, n)
                        inpset.incar_settings.update({x: v})
                        path = '%s_super%s_par%s%s%s' % (self.name, s, n, x, o)
                        inpset.incar_settings.update({'system': '%s_super%s' % (self.name, s)})
                        inpset.write_input(structure=struc, output_dir=path)
                        q = self.manager.qadapter
                        q.set_mpi_ncpus(n)
                        job_string = q.get_script_str(job_name=self.name+'s'+str(s)+'np'+str(n),
                                                      executable=self.subject,
                                                      launch_dir=path,
                                                      qerr_path=os.path.join(path, 'qerr.out'),
                                                      qout_path=os.path.join(path, 'qout.out'))
                        self.script_list.append(os.path.join(path, 'job.sh'))
                        f = open(self.script_list[-1], 'w')
                        f.write(job_string)
                        f.close()
        sys.stdout.write("|\n")
        sys.stdout.flush()
        return 0

    def create_job_collection(self):
        """
        create a single script file to submit all calculations

        :return 0 on succes
        """
        f = open('job_collection', 'w')
        for script in self.script_list:
            path = os.path.split(script)
            f.write('cd %s \nqsub %s \n cd .. \n' % path)
        f.close()
        return 0


def get_benchmark(**kwargs):
    return Benchmark(**kwargs)
