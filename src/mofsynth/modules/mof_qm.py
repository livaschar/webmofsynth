from dataclasses import dataclass
import os
import subprocess
from mofid.run_mofid import cif2mofid
from pymatgen.io.cif import CifWriter
from pymatgen.core.structure import IStructure
from . other_qm import copy
import numpy as np
import signal

@dataclass
class MOF:

    def __init__(self, name, synth_path):
        r"""
        Initialize a new MOF instance.
        """
        self.name = name
        self._initialize_paths(synth_path)
        self.linker_smiles = ''
        self.opt_energy = np.nan
        self.sp_energy = np.nan
        self.de = np.nan
        self.rmsd = np.nan


    def _initialize_paths(self, synth_path):
        r"""
        Initialize paths for the MOF instance.
        """
        self.init_path = os.path.join(synth_path, self.name)
        os.makedirs(self.init_path, exist_ok = True)
        self.fragmentation_path = os.path.join(synth_path, self.name, "fragmentation")
        os.makedirs(self.fragmentation_path, exist_ok = True)        
        self.cif2cell_path = os.path.join(synth_path, self.name, "cif2cell")
        os.makedirs(self.cif2cell_path, exist_ok = True)
        self.obabel_path = os.path.join(synth_path, self.name, "obabel")
        os.makedirs(self.obabel_path, exist_ok = True)
        self.xtb_path = os.path.join(synth_path, self.name, "xtb")
        os.makedirs(self.xtb_path, exist_ok = True)
        self.sp_path = os.path.join(self.xtb_path, "sp")
        os.makedirs(self.sp_path, exist_ok = True)
        self.rmsd_path = os.path.join(self.xtb_path, "rmsd")
        os.makedirs(self.rmsd_path, exist_ok = True)
    

    def create_supercell(self, limit, synth_path):
        r"""
        Create a supercell for the MOF instance.
        """        
        copy(self.init_path, self.cif2cell_path, f"{self.name}.cif")
        
        init_file = os.path.join(synth_path, self.name, "cif2cell", f'{self.name}.cif')
        rename_file = os.path.join(synth_path, self.name, "cif2cell", f'{self.name}_supercell.cif')

        try:
            structure = IStructure.from_file(init_file)
        except:
            return '0', f'Could not be parsed'
        
        if str(limit) != 'None' and all(cell_length > int(limit) for cell_length in structure.lattice.abc):
            os.rename(init_file, rename_file)
            supercell = structure
        else:
            supercell = structure * 2
        
        try:
            w = CifWriter(supercell)
            w.write_file(rename_file)
        except:
            return '2', f'Could not be writen with pymatgen. Consider changing the Supercell limit'

        copy(self.cif2cell_path, self.fragmentation_path, f"{self.name}_supercell.cif")

        return True, ''

    def fragmentation(self, synth_path):
        r"""
        Perform the fragmentation process for the MOF instance.

        """
        
        class TimeoutException(Exception):
            pass

        def handler(signum, frame):
            raise TimeoutException()

        signal.signal(signal.SIGALRM, handler)
        signal.alarm(10)  # timeout in seconds


        init_file = os.path.join(synth_path, self.name, "fragmentation", f"{self.name}_supercell.cif")
        
        try:
            cif2mofid(init_file, output_path=os.path.join(synth_path, self.name, "fragmentation/Output"))
        except TimeoutException:
                print(f"Timeout reached while Fragmentation {self.name}")
                signal.alarm(0)
                return 0, f'Fragmentation error. Timeout reached.'
        except:
            signal.alarm(0)
            return 0, f'Fragmentation error.'
    
        copy(os.path.join(self.fragmentation_path, "Output/MetalOxo"), self.obabel_path, "linkers.cif")
        
        signal.alarm(0)
        return 1, ''
 
    def obabel(self, synth_path):
        r"""
        Convert the linkers.cif file to XYZ and MOL formats and keep the longest linker contained in CIF file.

        """
        init_file = os.path.join(synth_path, self.name, "obabel", "linkers.cif")
        final_file = os.path.join(synth_path, self.name, "obabel", "linkers_prom_222.xyz")

        # ''' CIF TO XYZ '''
        command = ["obabel", "-icif", init_file, "-oxyz", "-O", final_file, "-r"]   
        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
        except:
            return 0, f'Obabel error. CIF to XYZ conversion.'
        
        xyz_file_initial = os.path.join(synth_path, self.name, "obabel", 'linkers_prom_222.xyz')
        xyz_file_final = os.path.join(synth_path, self.name, "obabel", 'linker.xyz')
        os.rename(xyz_file_initial, xyz_file_final)
        # ''' ----------- '''

        # ''' CIF TO SMI '''
        smi_file = os.path.join(synth_path, self.name, "obabel", 'linker.smi')
        command = ["obabel", xyz_file_final, "-xc", "-O", smi_file]
        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
        except:
            return 0, f'Obabel error. CIF to SMI conversion.'
        ''' ----------- '''
    
        copy(self.obabel_path, self.xtb_path, "linker.xyz")
        
        return 1, ''
            
    def single_point(self):
        r"""
        Perform a single-point calculation using XTB.
        """
        copy(self.xtb_path, self.sp_path, "linker.xyz")
        
        """ SINGLE POINT CALCULATION """
        job_sh_path = os.path.join(self.sp_path, 'job_sp.sh')
        run_str_sp = f'sbatch {job_sh_path}'
        try:
            p = subprocess.Popen(run_str_sp, shell=True, cwd=self.sp_path)
            p.wait()
        except:
            return 0, f"XTB single point error."

        return 1, ''

    def check_fragmentation(self):
        r"""
        Check if the fragmentation workflow successfully found any linkers in the supercell.
        """        
        file_size = os.path.getsize(os.path.join(self.fragmentation_path,"Output/MetalOxo/linkers.cif"))
        if file_size < 550:
            return False
        return True
    
    def check_smiles(self):
        r"""
        Check if the Smiles code file was successfully generated during the fragmentation process.
        """        
        file_size = os.path.getsize(os.path.join(self.fragmentation_path,"Output/python_smiles_parts.txt"))
        if file_size < 10:
            return False
        return True

    def find_unique_linkers(instances, path_to_linkers_directory):
        r"""
        Process MOF instances to assign unique identifiers to their SMILES codes and organize data for linkers.   
        """

        from . linkers_qm import Linkers

        # Iterate through mof instances
        unique_id = 0
        new_instances = []
        fault_smiles = []
        linker_instances = []
        smiles_id_dict = {}

        for instance in instances:
    
            # Take the smiles code for this linker
            smiles = MOF.find_smiles_obabel(instance.obabel_path)

            if smiles != None:
                new_instances.append(instance)
            else:
                fault_smiles.append(instance.name)
                continue

            # This sets the smile code equal to a unique id code
            if smiles not in smiles_id_dict.keys():
                unique_id += 1
                smiles_id_dict[smiles] = str(unique_id) # smiles - unique_id

            instance.linker_smiles = smiles_id_dict[smiles]

            linker = Linkers(instance.linker_smiles, instance.name, path_to_linkers_directory)
            linker_instances.append(linker)
            
            copy(instance.obabel_path, os.path.join(path_to_linkers_directory, instance.linker_smiles, instance.name), 'linker.xyz', 'linker.xyz')
        
        instances = new_instances

        return smiles_id_dict , new_instances, fault_smiles, linker_instances
    
    def find_smiles_obabel(obabel_path):
        r"""
        Extract Smiles code from the obabel-generated smi file.
        """
        smiles = None
        
        file_size = os.path.getsize(os.path.join(obabel_path, 'linker.smi'))

        file = os.path.join(obabel_path, 'linker.smi')

        if os.path.exists(file) and file_size > 9:
            with open(file) as f:
                lines = f.readlines()
            smiles = str(lines[0].split()[0])

        return smiles

    @staticmethod
    def analyse(cifs, linkers, best_opt_energy_dict, id_smiles_dict, df, src_dir):
        r"""
        Analyze MOF instances based on calculated energies and linkers information.
        """
        import pandas as pd
        from scipy.stats import percentileofscore

        results_list = []

        for mof in cifs:
            linker = next((obj for obj in linkers if obj.smiles_code == mof.linker_smiles and obj.mof_name == mof.name), None)

            with open(os.path.join(mof.sp_path, "check.out"), 'r') as f:
                lines = f.readlines()
            for line in lines:
                if "| TOTAL ENERGY" in line:
                    mof.sp_energy = float(line.split()[3])
                    break
            if linker != None and linker.smiles_code in best_opt_energy_dict.keys():
                mof.opt_energy = float(linker.opt_energy)
                mof.opt_status = linker.opt_status
                mof.calc_de(best_opt_energy_dict)
                mof.calc_rmsd(best_opt_energy_dict)
            
                # Create a new DataFrame row
                row = pd.DataFrame({
                    'NAME': [mof.name],
                    'ENERGY_(OPT-SP)_[kcal/mol]': [mof.de*627.51],
                    'RMSD_[A]': [mof.rmsd]
                    })
    
                df = pd.concat([df, row], ignore_index=True)
    
                # Sort by ENERGY_(OPT-SP)_[kcal/mol]
                df_sorted_energy = df.sort_values(by='ENERGY_(OPT-SP)_[kcal/mol]', ascending=True).reset_index(drop=True)
                df_sorted_energy['Energy_Rank'] = df_sorted_energy.index + 1
    
                # Sort by RMSD_[A]
                df_sorted_rmsd = df.sort_values(by='RMSD_[A]', ascending=True).reset_index(drop=True)
                df_sorted_rmsd['RMSD_Rank'] = df_sorted_rmsd.index + 1
                
                # Find the rank of the example
                energy_rank = df_sorted_energy[df_sorted_energy['NAME'] == mof.name]['Energy_Rank'].values[0]
                rmsd_rank = df_sorted_rmsd[df_sorted_rmsd['NAME'] == mof.name]['RMSD_Rank'].values[0]
                
                # Calculate percentile for energy
                energy_scores = df['ENERGY_(OPT-SP)_[kcal/mol]']
                energy_percentile = percentileofscore(energy_scores, mof.de*627.51, kind='weak')
                
                # Calculate percentile for RMSD
                rmsd_scores = df['RMSD_[A]']
                rmsd_percentile = percentileofscore(rmsd_scores, mof.rmsd, kind='weak')

                results_list.append([mof.name, round(100-energy_percentile, 1), round(rmsd_percentile, 1), round(mof.de, 1), round(mof.de * 627.51, 1), round(mof.rmsd, 2), mof.linker_smiles, id_smiles_dict[mof.linker_smiles], round(mof.sp_energy, 4), round(mof.opt_energy, 4), mof.opt_status])
            else:
                continue
        return results_list
    
    def calc_de(self, best_opt_energy_dict):
        r"""
        Calculate the binding energy (DE) for the MOF instance.
        """

        smiles = self.linker_smiles
        
        if smiles in best_opt_energy_dict and best_opt_energy_dict[smiles] is not None:
            best_opt_energy = best_opt_energy_dict[smiles][0]
            self.de = float(best_opt_energy) - float(self.sp_energy)
        else:
            self.de = 0
        
        return self.de

    def calc_rmsd(self, best_opt_energy_dict):
        r"""
        Calculate the RMSD (Root Mean Square Deviation) for the MOF instance.
        """
    
        rmsd = []        
    
        copy(best_opt_energy_dict[self.linker_smiles][1], self.rmsd_path, 'xtbopt.xyz', 'final_opt.xyz')
        copy(self.sp_path, self.rmsd_path, 'linker.xyz', 'final_sp.xyz')
        opt_file = os.path.join(self.rmsd_path, 'final_opt.xyz')
        sp_file = os.path.join(self.rmsd_path, 'final_sp.xyz')
        sp_mod_file = os.path.join(self.rmsd_path, 'final_sp_mod.xyz')
            
        check = MOF.rmsd_p(sp_file, opt_file, self.rmsd_path)
    
        try:
            for sp in [sp_file, sp_mod_file]:
                command = f"calculate_rmsd -e {opt_file} {sp}"
                rmsd.append(subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
        
                command = f"calculate_rmsd -e --reorder-method hungarian {opt_file} {sp}"
                rmsd.append(subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
            
                command = f"calculate_rmsd -e --reorder-method inertia-hungarian {opt_file} {sp}"
                rmsd.append(subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
            
                command = f"calculate_rmsd -e --reorder-method distance {opt_file} {sp}"
                rmsd.append(subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))        
        
        except Exception as e:
            
            print(f"An error occurred while running the command calculate_rmsd: {str(e)}")
            
            return 0, False
        
    
        try:
            minimum = float(rmsd[0].stdout)
            args = rmsd[0].args
        except:
            minimum = 10000
            print('WARNING: Error in float rmsd for: ', self.name, '\n')
            print(f"Warning: Unable to convert {rmsd[0].stdout} to float for {rmsd[0].args}")

        for i in rmsd:
            try:
                current_value = float(i.stdout)
                if current_value < minimum:
                    minimum = float(i.stdout)
                    args = i.args
            except ValueError:
                pass
    
        with open(os.path.join(self.rmsd_path, 'result.txt'), 'w') as file:
            file.write(str(minimum))
            file.write('\n')
            try:
                file.write(args)
            except:
                print(f'Args not found for mof {self.rmsd_path}')
                    
        self.rmsd = minimum
        
    @staticmethod
    def rmsd_p(sp_file, opt_file, rmsd_path, reorder = False, recursion_depth = 0):
        r"""
        Creating another instance using new reordering method not include in the original calculate_rmsd tool.

        Parameters
        ----------
        reorder : bool, optional
            Whether to perform reordering, by default False.
        recursion_depth : int, optional
            Recursion depth to handle potential errors, by default 0.

        Returns
        -------
        bool
            True if successful, False otherwise.
        """        
        # Define a dictionary to map atomic numbers to symbols
        atomic_symbols = {
            0: 'X', 1: 'H', 2: 'He', 3: 'Li', 4: 'Be', 5: 'B', 6: 'C', 7: 'N', 8: 'O', 9: 'F', 10: 'Ne',
            11: 'Na', 12: 'Mg', 13: 'Al', 14: 'Si', 15: 'P', 16: 'S', 17: 'Cl', 18: 'Ar',
            19: 'K', 20: 'Ca', 21: 'Sc', 22: 'Ti', 23: 'V', 24: 'Cr', 25: 'Mn', 26: 'Fe',
            27: 'Ni', 28: 'Co', 29: 'Cu', 30: 'Zn', 31: 'Ga', 32: 'Ge', 33: 'As', 34: 'Se',
            35: 'Br', 36: 'Kr', 37: 'Rb', 38: 'Sr', 39: 'Y', 40: 'Zr', 41: 'Nb', 42: 'Mo',
            43: 'Tc', 44: 'Ru', 45: 'Rh', 46: 'Pd', 47: 'Ag', 48: 'Cd', 49: 'In', 50: 'Sn',
            51: 'Sb', 52: 'Te', 53: 'I', 54: 'Xe', 55: 'Cs', 56: 'Ba', 57: 'La', 58: 'Ce',
            59: 'Pr', 60: 'Nd', 61: 'Pm', 62: 'Sm', 63: 'Eu', 64: 'Gd', 65: 'Tb', 66: 'Dy',
            67: 'Ho', 68: 'Er', 69: 'Tm', 70: 'Yb', 71: 'Lu', 72: 'Hf', 73: 'Ta', 74: 'W',
            75: 'Re', 76: 'Os', 77: 'Ir', 78: 'Pt', 79: 'Au', 80: 'Hg', 81: 'Tl', 82: 'Pb',
            83: 'Bi', 84: 'Po', 85: 'At', 86: 'Rn', 87: 'Fr', 88: 'Ra', 89: 'Ac', 90: 'Th',
            91: 'Pa', 92: 'U', 93: 'Np', 94: 'Pu', 95: 'Am', 96: 'Cm', 97: 'Bk', 98: 'Cf',
            99: 'Es', 100: 'Fm', 101: 'Md', 102: 'No', 103: 'Lr', 104: 'Rf', 105: 'Db', 106: 'Sg',
            107: 'Bh', 108: 'Hs', 109: 'Mt', 110: 'Ds', 111: 'Rg', 112: 'Cn', 113: 'Nh', 114: 'Fl',
            115: 'Mc', 116: 'Lv', 117: 'Ts', 118: 'Og',
        }
    
        if recursion_depth >= 3:
            print("Recursion depth limit reached. Exiting.")
            return False
        
        sp_mod_txt_path = os.path.join(rmsd_path, 'final_sp_mod.txt')
        sp_mod_xyz_path = os.path.join(rmsd_path, 'final_sp_mod.xyz')
        
        try:
            if reorder == False:
                os.system(f"calculate_rmsd -p {opt_file} {sp_file} > {sp_mod_txt_path}")
            else:
                os.system(f"calculate_rmsd -p --reorder {opt_file} {sp_file} > {sp_mod_txt_path}")
    
        except Exception as e:
            print(f"An error occurred while running the command calculate_rmsd: {str(e)}")
            return False
    
        data = []
        with open(sp_mod_txt_path, 'r') as input_file:
            lines = input_file.readlines()
    
            for line_number, line in enumerate(lines):
                
                atomic_number = 0
                if line_number < 2:
                    continue
                
                parts = line.split()
                if parts == []:
                    continue
    
                try:
                    atomic_number = int(parts[0])
                except ValueError:
                    input_file.close()
                    return MOF.rmsd_p(sp_file, opt_file, rmsd_path, reorder=True, recursion_depth=recursion_depth + 1)
    
                symbol = atomic_symbols.get(atomic_number)
                coordinates = [float(coord) for coord in parts[1:4]]
                data.append((symbol, coordinates))
        

        with open(sp_mod_xyz_path, 'w') as output_file:
            output_file.write(f"{len(data)}\n")
            output_file.write("\n")
            for symbol, coords in data:
                output_file.write(f"{symbol} {coords[0]:.6f} {coords[1]:.6f} {coords[2]:.6f}\n")
        
        return True