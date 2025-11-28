# This file is part of WEB MOF-Synth.
# Copyright (C) 2025 Charalampos G. Livas

# MOF-Synth is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import os
import json
import pickle
from . modules.mof_qm import MOF
from . modules.linkers_qm import Linkers
from . modules.user_qm import USER
from . modules.other_qm import (copy, load_objects, write_csv_results)

def main_run(directory, supercell_limit, EXECUTION_FOLDER):
    r"""
    Perform the synthesizability evaluation for MOFs in the specified directory.
    """
    print(f'  \033[1;32m\nSTART OF SYNTHESIZABILITY EVALUATION\033[m')
    discarded = {}

    # CONFIGURATION BLOCK
    unique_user = 'USER' + EXECUTION_FOLDER.split('/')[-1]
    user = USER(unique_user)
    user.src_dir = EXECUTION_FOLDER
    user.job_sh_path = os.path.join(EXECUTION_FOLDER, 'input_data')
    user.job_sh_sp = 'job_sp.sh'
    user.job_sh_opt = 'job_opt.sh'
    user.opt_cycles = 1000

    # Create the working directory
    user.synth_path = os.path.join(EXECUTION_FOLDER, 'Synth_folder')
    os.makedirs(user.synth_path, exist_ok=True)    

    # A list of cifs from the user specified directory
    user_dir = os.path.join(os.path.join(EXECUTION_FOLDER, directory))
    cifs = [item for item in os.listdir(user_dir) if item.endswith(".cif")]
    if cifs == []:
        return 0, 'CIF list is empty', '', []

    # Single Point procedure for each CIF
    for _, cif in enumerate(cifs):

        print(f'\n - \033[1;34mMOF under study: {cif[:-4]}\033[m -')

        # Initialize the mof name as an object of MOF class
        mof = MOF(cif[:-4], user.synth_path)
        user.instances.append(mof)

        # Copy .cif and job.sh in the single point mof directory
        copy(user_dir, mof.init_path, f"{mof.name}.cif")
        copy(user.job_sh_path, mof.sp_path, user.job_sh_sp)
        
        # Supercell, Fragmentation, Extract Linker, SP Energy
        supercell_check, message = mof.create_supercell(supercell_limit, user.synth_path)
        if supercell_check == '0':
            user.instances.pop()
            discarded[cif] = message
            continue
            
        elif supercell_check == '2':
            user.instances.pop()
            discarded[cif] = message
            continue
        
        fragmentation_check, message = mof.fragmentation(user.synth_path)
        if fragmentation_check == 0:
            user.instances.pop()
            discarded[cif] = message
            continue
            
        obabel_check, message = mof.obabel(user.synth_path)
        if obabel_check == 0:
            user.instances.pop()
            discarded[cif] = message
            continue
            
        single_point_check, message = mof.single_point()
        if single_point_check == 0:
            user.instances.pop()
            discarded[cif] = message
            continue

        # Check if supercell procedure runned correctly
        if supercell_check is False:
            user.fault_supercell.append(mof.name)
            user.instances.pop()
            discarded[cif] = message
            continue

        # Check if fragmentation procedure found indeed a linker
        fragm_check = mof.check_fragmentation()
        if fragm_check is False:
            user.fault_fragment.append(mof.name)
            user.instances.pop()
            discarded[cif] = message
            continue
    
    # Find the unique linkers from the whole set of MOFs
    user.path_to_linkers_directory = os.path.join(user.synth_path, '_Linkers_')
    smiles_id_dict , user.new_instances, user.fault_smiles, user.linker_instances = MOF.find_unique_linkers(user.instances, user.path_to_linkers_directory)

    # Proceed to the optimization procedure of every linker
    list_name_to_remove = []
    for linker in user.linker_instances:
        print(f'\n - \033[1;34mLinker under optimization study: {linker.smiles_code}, of {linker.mof_name}\033[m -')
        opt_check, message = linker.optimize(user.opt_cycles, user.job_sh_path, user.job_sh_opt)
        if opt_check == 0:
            # Assuming user.instances contains instances of the MOF class
            list_name_to_remove.append(linker.mof_name)
            discarded[linker.mof_name + '.cif'] = message
            continue
    
    # Create a set of names to remove for faster lookup
    names_to_remove_set = set(list_name_to_remove)
    # Filter instances based on the set
    user.instances = [instance for instance in user.instances if instance.name not in names_to_remove_set]
    user.linker_instances = [instance for instance in user.linker_instances if instance.mof_name not in names_to_remove_set]

    # Right instances of MOF class
    with open(os.path.join(EXECUTION_FOLDER, 'cifs.pkl'), 'wb') as file:
        pickle.dump(user.instances, file)
    
    # Right instances of Linkers class
    with open(os.path.join(EXECUTION_FOLDER, 'linkers.pkl'), 'wb') as file:
        pickle.dump(user.linker_instances, file)
    
    if user.fault_fragment != []:
        with open(os.path.join(EXECUTION_FOLDER, 'fault_fragmentation.txt'), 'w') as file:
            for mof_name in user.fault_fragment:
                file.write(f'{mof_name}\n')

    if user.fault_smiles != []:
        with open(os.path.join(EXECUTION_FOLDER, 'fault_smiles.txt'), 'w') as file:
            for mof_name in user.fault_smiles:
                file.write(f'{mof_name}\n')
    
    with open(os.path.join(EXECUTION_FOLDER, 'smiles_id_dictionary.txt'), 'w') as file:
        for key, value in smiles_id_dict.items():
            file.write(f'{key} : {value}\n')
    
    discarded_path = os.path.join(EXECUTION_FOLDER, 'discarded.json')
    with open(discarded_path, 'w') as json_file:
        json.dump(discarded, json_file, indent=4)  
    
    return 1, '', user, discarded

def check_opt(EXECUTION_FOLDER, len_files, user):
    r"""
    Check the optimization status of linker molecules.
    """    
    _, linkers, _= load_objects(EXECUTION_FOLDER)

    user.converged, user.not_converged = Linkers.check_optimization_status(linkers)
    print('  USER.CONVERGED:', len(user.converged))

    if len(user.converged) == 0:
        return -1, '', ''
        # return 0, 'Evaluation converged for 0 CIF files'
    
    elif len(user.not_converged) != 0:
        return 0, user.converged, user.not_converged
        # error = 'Evaluation did not converge at the time limit for:\n '
        # for name in user.not_converged:
        #     add = name + ', '
        #     error += add
        # return 0, f'{error}.\nPlease remove them from your uploads.'
    
    elif len(user.converged) == len_files:
        return 1, user.converged, user.not_converged
    else:
        return -1, 'Unknown problem in optimization check', ''


def handle_non_convergence(user, not_converged, discarded, execution_folder):
    """
    Handle instances that did not converge by updating the discarded dictionary,
    removing instances from user lists, and saving the updated lists to files.
    """
    list_not_converged = []
    # Update the discarded dictionary with messages
    for instance in not_converged:
        list_not_converged.append(instance.mof_name)
        discarded[instance.mof_name] = 'Optimization did not converge at a certain time limit'
    
    discarded_path = os.path.join(execution_folder, 'discarded.json')
    with open(discarded_path, 'w') as json_file:
        json.dump(discarded, json_file, indent=4)  
    
    # Create a set of names to remove for faster lookups
    names_to_remove_set = set(list_not_converged)
    
    # Filter out non-converged instances
    user.instances = [instance for instance in user.instances if instance.name not in names_to_remove_set]
    user.linker_instances = [instance for instance in user.linker_instances if instance.mof_name not in names_to_remove_set]
    
    # Save the updated instances to pickle files
    with open(os.path.join(execution_folder, 'cifs.pkl'), 'wb') as file:
        pickle.dump(user.instances, file)
    
    with open(os.path.join(execution_folder, 'linkers.pkl'), 'wb') as file:
        pickle.dump(user.linker_instances, file)


def export_results(EXECUTION_FOLDER, user):
    from . modules.other_qm import load_objects
    import pandas as pd
        
    cifs, linkers, id_smiles_dict = load_objects(EXECUTION_FOLDER)

    user.converged, user.not_converged = Linkers.check_optimization_status(linkers)

    for linker in user.converged:
        linker.read_linker_opt_energies()
    
    # Best opt for each smiles code. {smile code as keys and value [opt energy, opt_path]}
    best_opt_energy_dict = Linkers.define_best_opt_energy(user.converged)
    
    file_path = os.path.join(EXECUTION_FOLDER, 'input_data/databases.xlsx')
    df = pd.read_excel(file_path)

    results_list = MOF.analyse(cifs, linkers, best_opt_energy_dict, id_smiles_dict, df, user.src_dir)

    user.results_csv_path = os.path.join(user.synth_path, f'{user.output_file_name}.csv')
    write_csv_results(results_list, os.path.join(EXECUTION_FOLDER, user.results_csv_path))    
    return 1, 'Evaluation was succesful. Results are ready.'
