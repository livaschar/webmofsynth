import shutil
import pickle
import os
import csv


def load_objects(path):
    
    id_smiles_dict = {}
    cifs_pkl = os.path.join(path, 'cifs.pkl')
    linkers_pkl = os.path.join(path, 'linkers.pkl')
    smiles_id_dictionary = os.path.join(path, 'smiles_id_dictionary.txt')

    with open(cifs_pkl, 'rb') as file:
        cifs = pickle.load(file)
    with open(linkers_pkl, 'rb') as file:
        linkers = pickle.load(file)
    
    with open(smiles_id_dictionary, 'r') as file:
        lines = file.readlines()
        for line in lines:
            id_smiles_dict[line.split()[-1]] = line.split()[0]
    
    return cifs, linkers, id_smiles_dict


def copy(path1, path2, file_1, file_2 = None):
    
    if file_2 is None:
        file_2 = file_1
    
    shutil.copy(os.path.join(path1, file_1), os.path.join(path2, file_2))

    return


def write_csv_results(results_list, results_csv_path):
    
    headers = ["Index", "Filename", "Energy Percentile Rank (%)", "RMSD Percentile Rank (%)", "Energy (kcal/mol)", "RMSD (A)", "Smiles", "Single Point Energy (au)", "Optimized Energy (au)", "Status"]    
    
    sorted_results = sorted(results_list, key=lambda x: float(x[1]))
    
    # Open the CSV file for writing
    with open(results_csv_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        
        # Write headers
        writer.writerow(headers)
        
        # Write results
        for index, result_row in enumerate(sorted_results):
            row_data = [index+1, result_row[0], result_row[1], result_row[2], result_row[4], result_row[5], result_row[7], result_row[8], result_row[9], result_row[10]]
            writer.writerow(row_data)
