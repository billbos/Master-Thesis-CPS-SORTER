import os
import csv
import json
import sys

def json_files_to_csv(directory, outputfile, max_num_files=10): 
    '''
    creates a csv file out of json files from beamng data with following rows:
    test
    '''
    with open('{}.csv'.format(outputfile), 'w', newline='') as csv_file:
        fieldnames = ['filename','avg_distance','reason', 'num_oob_straight', 'num_oob_left', 'num_oob_right', 'total_seg', 'combination_of_seg', 'total_turn_angle', 'max_turn_angle', 'avg_turn_angle', 'num_of_oobs','max_distance']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        counter = 0
        for subdir, dirs, files in os.walk(directory):
            for filename in files:
                filepath = subdir + os.sep + filename
                if filepath.endswith(".json"):
                    with open(filepath) as json_file:
                        try:
                            data = json.load(json_file)
                            writer.writerow(extract_data(os.path.basename(filepath), data))
                            counter += 1
                            if counter > max_num_files:
                                print('Rows: {}'.format(counter))
                                return
                            print(counter)
                        except Exception as e:
                            print(e, os.path.basename(filepath))

def extract_data(filename, data):
    result = {
        'filename': filename,
        'num_of_oobs': data['oobs'],
        'max_distance': data['maximum_distance'],
        'avg_distance': data['average_distance'],
        'reason': data['reason'],
        'num_oob_straight': 0,
        'num_oob_left': 0,
        'num_oob_right': 0,
        'total_turn_angle': 0,
        'max_turn_angle': 0,
        'avg_turn_angle': 0,
        'total_seg': 0,
        'combination_of_seg': 0
    }
   
    total_occ = 0
    for seg, occurence in data['seg_oob_count'].items():
        splitted_seg = seg.split('_')
        total_occ  += occurence
        if splitted_seg[0] == 'l':
            abs_turn_angle = abs(int(splitted_seg[2]))
            result['num_oob_left'] += occurence
            result['total_turn_angle'] += abs_turn_angle
            if result['max_turn_angle'] < abs_turn_angle:
                result['max_turn_angle'] = abs_turn_angle
        if splitted_seg[0] == 'r':
            abs_turn_angle = abs(int(splitted_seg[2]))
            result['num_oob_right'] += occurence
            result['total_turn_angle'] += abs_turn_angle
            if result['max_turn_angle'] < abs_turn_angle:
                result['max_turn_angle'] = abs_turn_angle
        if splitted_seg[0] == 'straight':
            result['num_oob_straight'] += occurence

    result['total_seg'] = total_occ

    if result['num_oob_straight']>0:
        result['combination_of_seg'] += 1
    if result['num_oob_left']>0:
        result['combination_of_seg'] += 3
    if result['num_oob_right']>0:
        result['combination_of_seg'] += 5
    
    if total_occ == 0:
        total_occ = 1
        
    result['avg_turn_angle'] = result['total_turn_angle'] / (total_occ)
    return result



if __name__ == '__main__':
    directory = 'D:/master thesis/DataSet'
    json_files_to_csv(directory, 'test', 4000)