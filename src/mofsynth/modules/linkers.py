from dataclasses import dataclass
import os
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
        self.opt_path = os.path.join(path_to_linkers_directory, self.smiles_code, self.mof_name)
        self.opt_energy = 0
        self.opt_status = 'not_converged'

        try:
            os.makedirs(self.opt_path, exist_ok = True)
        except:
            return None

    def optimize(self, opt_cycles, job_sh_path, job_sh_opt):
        r"""
        Optimize the linker structure.
        """
        
        # Must be before os.chdir(self.opt_path)
        copy(job_sh_path, self.opt_path, job_sh_opt)
        job_sh_path = os.path.join(self.opt_path, job_sh_opt)
        run_str_opt = f'sbatch {job_sh_path}'
        try:
            p = subprocess.Popen(run_str_opt, shell=True, cwd=self.opt_path)
            p.wait()
        except:
            return 0, f"XTB optimization error"
        
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

            opt_output_file = os.path.join(linker.opt_path,"check.out")
            
            try:
                with open(opt_output_file, 'r') as f:
                    content = f.read()
            except:
                linker.opt_status = 'no_output_file'
                not_converged.append(linker)
                print(f'    Still running')
                continue
            # Check convergence status
            if "GEOMETRY OPTIMIZATION CONVERGED" in content:
                print(f'    CONVERGED: {linker.mof_name}')
                linker.opt_status = 'converged'
                converged.append(linker)
            elif "FAILED TO CONVERGE GEOMETRY OPTIMIZATION" in content:
                print(f'    NOT CONVERGED: {linker.mof_name}')
                linker.opt_status = 'not_converged'
                not_converged.append(linker)

        return converged, not_converged
    
    def read_linker_opt_energies(self):   
        r"""
        Read the optimization energy for a converged linker instance.
        """
        with open(os.path.join(self.opt_path, 'check.out')) as f:
            lines = f.readlines()
        for line in lines:
            if "| TOTAL ENERGY" in line:
                try:
                    self.opt_energy = float(line.split()[3])
                    print(f'Opt energy:{self.opt_energy}')
                except:
                    self.opt_energy = 0
                break

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