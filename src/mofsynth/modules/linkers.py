
from dataclasses import dataclass
import os
import re
from . other import copy
from . mof import MOF
import subprocess


@dataclass
class Linkers:
    r"""
    Class for managing linker molecules and their optimization.

    """

    def __init__(self, smiles_code, mof_name, path_to_linkers_directory):
        r"""
        Initialize a Linkers instance.
        """

        self.smiles_code = smiles_code
        self.mof_name = mof_name
        self.opt_path = os.path.join(path_to_linkers_directory, self.smiles_code, self.mof_name) #!!!!!!!!!
        self.opt_energy = 0
        self.opt_status = 'not_converged'

        try:
            os.makedirs(self.opt_path, exist_ok = True)
        except:
            return None

    def optimize(self, opt_cycles, job_sh_path, job_sh):
        r"""
        Optimize the linker structure.
        """
        
        # Must be before os.chdir(self.opt_path)
        copy(job_sh_path, self.opt_path, job_sh)
        
        init_file = os.path.join(self.opt_path, "linker.xyz")
        final_file = os.path.join(self.opt_path, "final.xyz")
        self.run_str_sp =  f"bash -l -c 'module load turbomole/7.02; x2t {init_file} > coord; uff; t2x -c > {final_file}'"

        try:
            p = subprocess.Popen(self.run_str_sp, shell = True, cwd=self.opt_path)
            p.wait()
        except:
            return 0, f"Turbomole optimization procedure"

        with open(os.path.join(self.opt_path, "control"), 'r') as f:
            lines = f.readlines()
        words = lines[2].split()
        words[0] = str(opt_cycles)
        lines[2] = ' '.join(words) +'\n'
        with open(os.path.join(self.opt_path, "control"),'w') as f:
            f.writelines(lines)

        job_sh_path = os.path.join(self.opt_path, 'job.sh')
        self.run_str = f'sbatch {job_sh_path}'
        try:
            p = subprocess.Popen(self.run_str, shell=True, cwd=self.opt_path)
            p.wait()
        except:
            return 0, f"Turbomole optimization procedure"
        
        return 1, ''
    
    @classmethod
    def check_optimization_status(cls, linkers_list):
        r"""
        Check the optimization status of linker instances.
        """
        converged = []
        not_converged = []

        for linker in linkers_list:
            print(f'  LINKER: {linker.mof_name}')

            if os.path.exists(os.path.join(linker.opt_path, 'uffconverged')):
                print(f'    CONVERGED: {linker.mof_name}')
                converged.append(linker)
                linker.opt_status = 'converged'
        
            elif os.path.exists(os.path.join(linker.opt_path, 'not.uffconverged')):
                print(f'    NOT CONVERGED: {linker.mof_name}')
                not_converged.append(linker)
            else:
                not_converged.append(linker)
                print(f'    Still running')

            
        return converged, not_converged
    
    def read_linker_opt_energies(self):   
        r"""
        Read the optimization energy for a converged linker instance.
        """        
        with open(os.path.join(self.opt_path, 'uffenergy')) as f:
            lines = f.readlines()
        
        self.opt_energy = lines[1].split()[-1]

        return self.opt_energy

    def define_best_opt_energy(converged):
        best_opt_energy_dict = {}

        for instance in converged:
            if instance.smiles_code in best_opt_energy_dict:
                if float(instance.opt_energy) < float(best_opt_energy_dict[instance.smiles_code][0]):
                    best_opt_energy_dict[instance.smiles_code] = [instance.opt_energy, instance.opt_path]
            else:
                best_opt_energy_dict[instance.smiles_code] = [instance.opt_energy, instance.opt_path]
                
        return best_opt_energy_dict