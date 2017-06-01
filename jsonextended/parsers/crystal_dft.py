#!/usr/bin/env python
# -- coding: utf-8 --

from jsonextended.parsers.base import BasicParser

class CrystalDFTParser(BasicParser):
    """ a class for parsing Crystal DFT Simulation Data

    format:

        meta
        initial
        #scf TODO
        optimisation
               step
                   <number>
        optimised

    """
    def _eval_intial_data(self):
        if self._has_sig('date:'):
            self.add_data('start date',' '.join(self._get_fields_after(1)),['meta'])
        if self._has_sig('input:'):
            self.add_data('input',' '.join(self._get_fields_after(1)),['meta'])

    def _eval_geom_data(self):

        if self._has_sig('* CRYSTAL14 *'):
            self._update_file_section('initial',level=1)

        if self._has_sig('STARTING GEOMETRY OPTIMIZATION'):
            self._update_file_section('optimisation',level=1)
            self._update_file_section('steps',level=2)

        if self._has_sig('* OPT END -'):
            self._update_file_section('optimised',level=1)
            if self._get_fields(5) == 'CONVERGED':
                self.add_data('converged',True,['meta'])
            else:
                self.add_data('converged',False,['meta'])
            self.add_data('energy',self._get_fields(8),
                          self._get_section(),dtype=float)

        if self._has_sig('COORDINATE AND CELL OPTIMIZATION - POINT'):
            if self._get_section()[0] == 'optimisation':
                config_number = self._get_fields(7)
                self._update_file_section(config_number, level=3)
                self.add_data('step',config_number,
                              init_keys=self._get_section(),
                              dtype=int)

        if self._has_sig({1:'PRIMITIVE',2:'CELL',7:'VOLUME=',10:'DENSITY'}):
            self.add_data(['volume','density'],self._get_fields([8,11]),
                                 init_keys=self._get_section()+['primitive'],
                                 dtype=float)
            self._skip_lines()
            assert self._has_sig('A B C ALPHA BETA GAMMA')
            self._skip_lines()
            self.add_data(['a','b','c','alpha','beta','gamma'],
                                self._get_fields([1,2,3,4,5,6]),
                                init_keys=self._get_section()+['primitive','lattice_parameters'],
                                dtype=float)

        if self._has_sig('ATOMS IN THE ASYMMETRIC UNIT'):
            self._skip_lines(3)
            cdict = self._table_todict(['id','assym','atomic_number','label','x/a','y/b','z/c'],
                                [int,self._str_map({'T':True,'F':False}),int,str,float,float,float])
            self.add_data('geometry',cdict,merge=True,
                                init_keys=self._get_section()+['primitive'])

        if self._has_sig('CRYSTALLOGRAPHIC CELL (VOLUME='):
            self.add_data('volume',self._get_fields(4)[0:-1],
                                 init_keys=self._get_section()+['crystallographic'],
                                 dtype=float)
            self._skip_lines()
            assert self._has_sig('A B C ALPHA BETA GAMMA')
            self._skip_lines()
            self.add_data(['a','b','c','alpha','beta','gamma'],
                                self._get_fields([1,2,3,4,5,6]),
                                 init_keys=self._get_section()+['crystallographic','lattice_parameters'],
                                 dtype=float)

        if self._has_sig('COORDINATES IN THE CRYSTALLOGRAPHIC CELL'):
            self._skip_lines(3)
            cdict = self._table_todict(['id','assym','atomic_number','label','x/a','y/b','z/c'],
                                [int,self._str_map({'T':True,'F':False}),int,str,float,float,float])
            self.add_data('geometry',cdict,merge=True,
                                 init_keys=self._get_section()+['crystallographic'])

        if self._has_sig('DIRECT LATTICE VECTORS CARTESIAN COMPONENTS'):
            self._skip_lines(2)
            self.add_data('a',[float(v) for v in self._get_fields([1,2,3])],
                                init_keys=self._get_section()+['crystallographic','lattice_vectors'])
            self._skip_lines(1)
            self.add_data('b',[float(v) for v in self._get_fields([1,2,3])],
                                init_keys=self._get_section()+['crystallographic','lattice_vectors'])
            self._skip_lines(1)
            self.add_data('c',[float(v) for v in self._get_fields([1,2,3])],
                                init_keys=self._get_section()+['crystallographic','lattice_vectors'])

        if self._has_sig('CARTESIAN COORDINATES - PRIMITIVE CELL'):
            self._skip_lines(4)
            cdict = self._table_todict(['id','atomic_number','label','x','y','z'],
                                    [int,int,str,float,float,float])
            self.add_data('geometry',cdict,merge=True,
                                 init_keys=self._get_section()+['primitive'])

        if self._has_sig('TOTAL ENERGY(DFT)(AU)('):
            self._line = self._line.replace('TOTAL ENERGY(DFT)(AU)(','') # ) touches energy value
            self.add_data('energy',self._get_fields(2),
                          init_keys=self._get_section(),
                          dtype=float)
