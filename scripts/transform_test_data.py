import os
import csv
import json
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import shutil
import re

class Point:
    def __init__(self,x_init,y_init):
        self.x = x_init
        self.y = y_init

    def shift(self, x, y):
        self.x += x
        self.y += y

    def __repr__(self):
        return "".join(["Point(", str(self.x), ",", str(self.y), ")"])
    
    def __eq__(self, other):
        if (self.x == other.x) and (self.y == other.y):
            return True
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)


class DataSetGenerator:
    '''
    Helper to generate training and datasets
    '''

    label_map = {
        'unsafe': 0,
        'safe': 1
    }
    reverse_label_map = {
        0: 'unsafe',
        1: 'safe'
    }

    def __init__(self, output_folder='C:\workspace\Master Thesis\datasets'):            
        self.output_folder = output_folder


    def create_training_test_set(self, data_set, split_ratio):
        file_name = data_set.split('.')[-2]
        output_folder = '{}/{}'.format(self.output_folder, file_name)
        if not os.path.exists(output_folder):
            os.mkdir(output_folder)
        df = pd.read_csv(data_set)
        df['safety'] = df['safety'].map(self.label_map)

        is_safe = df['safety'] == 1
        not_safe = df['safety'] == 0

        df_safe = df[is_safe]
        df_not_safe = df[not_safe]
        num_not_safe = int(len(df_not_safe) * split_ratio)

        sample_safe = df_safe.sample(n=num_not_safe, random_state=1)
        sample_unsafe = df_not_safe.sample(n=num_not_safe, random_state=1)

        training_set = pd.concat([sample_safe, sample_unsafe])
        test_set = df.drop(training_set.index)

        training_set = self.min_max_normalize(training_set)
        test_set = self.min_max_normalize(test_set)

        training_set['safety'] = training_set['safety'].map(self.reverse_label_map)
        test_set['safety'] = test_set['safety'].map(self.reverse_label_map)

        training_set.to_csv('{}/{}_{}_training_set.csv'.format(output_folder, split_ratio, file_name), index=False)
        test_set.to_csv('{}/{}_{}_test_set.csv'.format(output_folder, split_ratio, file_name), index=False)
        return output_folder

    def transform_to_test_data(self, directory, outputfile, ai_type='beamng'): 
        '''
        creates a csv file out of json files from beamng data
        '''
        file_pairs = self.search_files(directory)
        counter = 0
        # outputfile = '{}/{}'.format(self.output_folder, outputfile)
        outputfile = '{}_{}'.format(ai_type, outputfile)
        with open(outputfile, 'w', newline='') as csv_file:
            fieldnames = ['distance', 'road_distance', 'num_l_turns','num_r_turns','num_straights','median_angle','total_angle','mean_angle','std_angle',
            'max_angle','min_angle','median_pivot_off','mean_pivot_off','std_pivot_off','max_pivot_off','min_pivot_off', 'safety']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()          
            for filename, file_paths in file_pairs[ai_type].items():
                with open(file_paths['exec_file']) as json_file:
                    try:
                        data = json.load(json_file)
                        if not 'execution' in data.keys():
                            continue
                        test_data = self.extract_test_data(data)
                        print('file: {}'.format(counter))
                        counter += 1
                        writer.writerow(test_data)
                    except Exception as e:
                        print(e)
            
        return outputfile

    def min_max_normalize(self, dataset):
        dataNorm=((dataset-dataset.min())/(dataset.max()-dataset.min()))
        dataNorm["safety"]=dataset["safety"]
        return dataNorm

    def search_files(self, folder):
        beamng_pattern = re.compile(r".*beamng.*")
        deepdrive_pattern = re.compile(r".*deepdrive.*")
        file_pairs = {
            'beamng': {},
            'deepdrive': {}
        }
        for subdir, dirs, files in os.walk(directory):
            for filename in files:
                splited_subdir = subdir.split('\\')
                dir_name = splited_subdir[-1]
                filepath = subdir + os.sep + filename
                if dir_name in ['execs', 'tests', 'final']:
                    if beamng_pattern.match(filepath):
                        file_pairs['beamng'].setdefault('{}-{}'.format(splited_subdir[-3],filename), {}).update({'exec_file': filepath})
                    elif deepdrive_pattern.match(filepath):
                        file_pairs['deepdrive'].setdefault('{}-{}'.format(splited_subdir[-3],filename), {}).update({'exec_file': filepath})
        return file_pairs


    def extract_test_data(self, data):
        angles = []
        path = data['path']
        direct_distance = self.get_distance(Point(data['start'][0], data['start'][1]), Point(data['goal'][0], data['goal'][1]))
        road_distance = 0
        pivot_offs = []
        points = {}
        l_turns = 0
        r_turns = 0
        straight = 0
        road_distance = 0
        for seg_id, seg in data['network']['nodes'].items():
            if not int(seg_id) in data['path']:
                continue
            if seg['roadtype'] == 'r_turn':
                r_turns += 1
            elif seg['roadtype'] == 'l_turn':
                l_turns += 1
            elif seg['roadtype'] == 'straight':
                straight += 1

            if seg['angle'] != 0:
                angles.append(seg['angle'])
            if seg['pivot_off'] != 0:
                pivot_offs.append(seg['pivot_off'])
            
            points[seg_id] = Point(seg['x'], seg['y'])

        for i in range(0, len(path)-1):
            road_distance += self.get_distance(points[str(path[i])], points[str(path[i+1])])

        max_distance = data['execution']['maximum_distance']
        avg_distance = data['execution']['average_distance']

        if data['execution']['oobs'] > 0 and max_distance >= 3:
            safety = 'unsafe'
        else:
            safety = 'safe'
        
        result = {
            'distance': direct_distance,
            'road_distance': road_distance,
            'num_l_turns': l_turns,
            'num_r_turns': r_turns,
            'num_straights': straight,
            'median_angle': np.median(angles),
            'total_angle': np.sum(angles),
            'mean_angle': np.mean(angles),
            'std_angle': np.std(angles),
            'max_angle': np.max(angles),
            'min_angle': np.min(angles),
            'median_pivot_off': np.median(pivot_offs),
            'mean_pivot_off': np.mean(pivot_offs),
            'std_pivot_off': np.std(pivot_offs),
            'max_pivot_off': np.max(pivot_offs),
            'min_pivot_off': np.min(pivot_offs),
            'safety': safety
        }
    

        return result

    def get_distance(self, point_a, point_b):
        return np.sqrt( ((point_a.x-point_b.x)**2)+((point_a.y-point_b.y)**2))

    def analyse_data_structure(self, directory):
        counter_execution = 0
        counter_not_execution = 0
        files_name = {}
        dublicates = 0
        for subdir, dirs, files in os.walk(directory):
            for filename in files:
                splited_subdir = subdir.split('\\')
                dir_name = splited_subdir[-1]
                filepath = subdir + os.sep + filename
                with open(filepath) as json_file:
                    try:
                        data = json.load(json_file)
                        if not 'execution' in data.keys():
                            counter_not_execution += 1
                        else:
                            if files_name.get('{}-{}'.format(splited_subdir[-3],filename), False):
                                dublicates += 1
                            else:
                                files_name['{}-{}'.format(splited_subdir[-3],filename)] = 1

                            counter_execution += 1
                    except Exception as e:
                        print('file: {}, error: {}'.format(filename, e))
        print('counter_no_execution: {}, counter_execution: {}, dublicates: {}'.format(counter_not_execution, counter_execution, dublicates))

        return counter_not_execution, counter_execution


if __name__ == '__main__':
    directory = 'D:/master thesis/DataSet'
    # print(sys.argv)
    data_set_generator = DataSetGenerator()
    data_set = data_set_generator.transform_to_test_data(directory, sys.argv[1], 'deepdrive')
    new_dir = data_set_generator.create_training_test_set(data_set, float(sys.argv[2]))
    shutil.move(data_set, '{}/{}'.format(new_dir, sys.argv[1]))
    data_set = data_set_generator.transform_to_test_data(directory, sys.argv[1], 'beamng')
    new_dir = data_set_generator.create_training_test_set(data_set, float(sys.argv[2]))
    shutil.move(data_set, '{}/{}'.format(new_dir, sys.argv[1]))
    # data_set_generator.search_files(directory)
    # analyse_data_structure(directory)