import os
from os import listdir
from os.path import isfile, join
import csv
import json
import sys
import uuid
from pathlib import Path
import pandas as pd
import numpy as np
import shutil
import re
from asfault.tests import RoadTest
import os.path
import subprocess
from scipy.spatial.distance import directed_hausdorff
import random
from datetime import datetime
import numpy as np
import tempfile
from shutil import copyfile



PREDICTION_JAR = 'C:/workspace/MasterThesis/scripts/jars/makePrediction.jar'
MODEL_BUILDING_JAR = 'C:/workspace/MasterThesis/scripts/jars/train_models.jar'

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

    def __init__(self, output_folder='C:/workspace/MasterThesis/datasets'):            
        self.output_folder = output_folder


    def create_training_test_set(self, data_set, split_ratio, should_normalize=False):
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
        num_safe = int(len(df_safe) * split_ratio)
        if num_safe >= num_not_safe:
            num_sample = num_not_safe
            remaining_num = len(df_not_safe) - num_sample
        else:
            num_sample = num_safe
            remaining_num = len(df_safe) - num_sample


        sample_safe = df_safe.sample(n=num_sample, random_state=1)
        sample_unsafe = df_not_safe.sample(n=num_sample, random_state=1)


        remaining_safe = df_safe.drop(sample_safe.index)
        remaining_unsafe = df_not_safe.drop(sample_unsafe.index)
        num_safe = len(remaining_safe)
        num_unsafe  = len(remaining_unsafe)
        training_set = pd.concat([sample_safe, sample_unsafe])
        test_set = df.drop(training_set.index)

        sample_safe_test_balance = remaining_safe.sample(n=remaining_num, random_state=1)
        sample_unsafe_test_balance = remaining_unsafe.sample(n=remaining_num, random_state=1)

        balanced_set = pd.concat([sample_safe_test_balance, sample_unsafe_test_balance])

        if should_normalize:
            training_set = self.min_max_normalize(training_set)
            test_set = self.min_max_normalize(test_set)
            balanced_set = self.min_max_normalize(balanced_set)

        training_set['safety'] = training_set['safety'].map(self.reverse_label_map)
        test_set['safety'] = test_set['safety'].map(self.reverse_label_map)
        balanced_set['safety'] = balanced_set['safety'].map(self.reverse_label_map)


        training_path = '{}/training.csv'.format(output_folder)
        test_path = '{}/test.csv'.format(output_folder)
        test_balanced_path = '{}/balanced_test.csv'.format(output_folder)

        # training_path_arff = '{}/training.arff'.format(output_folder)
        # test_path_arff = '{}/test.arff'.format(output_folder)
        # test_balanced_path_arff = '{}/balanced_test.arff'.format(output_folder)


        training_set.to_csv(training_path, index=False)
        test_set.to_csv(test_path, index=False)
        balanced_set.to_csv(test_balanced_path, index=False)


        # pandas2arff(training_set, training_path_arff, cleanstringdata=True, cleannan=True)
        # pandas2arff(test_set, test_path_arff, cleanstringdata=True, cleannan=True)
        # pandas2arff(balanced_set, test_balanced_path_arff, cleanstringdata=True, cleannan=True)

        return output_folder, training_path, test_path, test_balanced_path

    def transform_to_test_data(self, directory, outputfile, ai_type='beamng'): 
        '''
        creates a csv file out of json files from beamng data
        '''
        file_pairs = self.search_files(directory)
        counter = 0
        # outputfile = '{}/{}'.format(self.output_folder, outputfile)
        # outputfile = '{}_{}'.format(ai_type, outputfile)
        with open(outputfile, 'w', newline='') as csv_file:
            # fieldnames = ['direct_distance', 'road_distance', 'num_l_turns','num_r_turns','num_straights','median_angle','total_angle','mean_angle','std_angle',
            # 'max_angle','min_angle','median_pivot_off','mean_pivot_off','std_pivot_off','max_pivot_off','min_pivot_off', 'ai', 'safety']
            fieldnames = ['direct_distance', 'road_distance', 'num_l_turns','num_r_turns','num_straights','median_angle','total_angle','mean_angle','std_angle',
            'max_angle','min_angle','median_pivot_off','mean_pivot_off','std_pivot_off','max_pivot_off','min_pivot_off', 'safety']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            # ais = ['beamng', 'driver_ai']
            # for ai_type in ais:
            for filename, file_paths in file_pairs[ai_type].items():
                with open(file_paths['exec_file']) as json_file:
                    try:
                        data = json.load(json_file)
                        if not 'execution' in data.keys():
                            continue
                        test_data = self.extract_test_data(data)
                        print('file: {}'.format(counter))
                        # test_data['ai'] = ai_type
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
        driver_ai_pattern = re.compile(r".*driver_ai.*")
        # default_pattern = re.compile(r".*")
        file_pairs = {
            'beamng': {},
            'deepdrive': {},
            'driver_ai': {},
            'default': {}
        }
        for subdir, dirs, files in os.walk(folder):
            for filename in files:
                splited_subdir = subdir.split('\\')
                dir_name = splited_subdir[-1]
                filepath = subdir + os.sep + filename
                # if dir_name in ['execs', 'tests', 'final']:
                if beamng_pattern.match(filepath):
                    file_pairs['beamng'].setdefault('{}-{}'.format(splited_subdir[-1],filename), {}).update({'exec_file': filepath})
                elif deepdrive_pattern.match(filepath):
                    file_pairs['deepdrive'].setdefault('{}-{}'.format(splited_subdir[-1],filename), {}).update({'exec_file': filepath})
                elif driver_ai_pattern.match(filepath):
                    file_pairs['driver_ai'].setdefault('{}-{}'.format(splited_subdir[-1],filename), {}).update({'exec_file': filepath})
                else:
                    file_pairs['default'].setdefault('{}-{}'.format(splited_subdir[-1],filename), {}).update({'exec_file': filepath})

        return file_pairs

    def extract_features_for_test_case(self, test_file, exclude_features=[]):
        try:
            with open(test_file) as json_file:
                data = json.load(json_file)
                features = self.extract_features(data)
                for f in exclude_features:
                    features.pop(f, None)
                    
                return features
        except Exception as e:
                print(e)

    def extract_features(self, data):
        angles = []
        path = data['path']
        path_used = []
        road_distance = 0
        pivot_offs = []
        points = {}
        l_turns = 0
        r_turns = 0
        straight = 0
        road_distance = 0

        for seg_id in path:
            seg = data['network']['nodes'][str(seg_id)]
            if seg['roadtype'] == 'r_turn':
                r_turns += 1
            elif seg['roadtype'] == 'l_turn':
                l_turns += 1
            elif seg['roadtype'] == 'straight':
                straight += 1

            if seg['angle'] < 0:
                seg['angle'] += 360
            if seg['angle'] > 0:
                angles.append(seg['angle'])
            if seg['pivot_off'] > 0:
                pivot_offs.append(seg['pivot_off'])
            
            points[seg_id] = Point(seg['x'], seg['y'])
            path_used.append(seg_id)

        if not angles:
            pivot_offs.append(0)
 
        if not pivot_offs:
            pivot_offs.append(0)   

        for i in range(0, len(path_used)-1):
            road_distance += self.get_distance(points[path_used[i]], points[path_used[i+1]])
        direct_distance = self.get_distance(points[path_used[0]], points[path_used[-1]])

        if data['execution']['oobs'] > 0:
            safety = 'unsafe'
        else:
            safety = 'safe'

        result = {
            'direct_distance': direct_distance,
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

    def extrac_segment_feature(self, data, feature_to_exclude=[]):
        rows = []
        path = data['network']['path']
        for i in range(0, len(path)):
            row = {
                'is_start_seg': 0,
                'is_last_seg': 0,
            }
            seg_id = path[i]
            seg = data['network']['nodes'][str(seg_id)]
            prev_seg = next_seg = None
            if i == 0:
                row['is_start_seg'] = 1
            else:
                prev_seg = data['network']['nodes'][str(path[i-1])]
            if i == len(path)-1:
                row['is_last_seg'] = 1
            else:
                next_seg = data['network']['nodes'][str(path[i+1])]
                
            row.update(self.segment_to_feature(seg, prev_seg, next_seg))
            for f in feature_to_exclude:
                row.pop(f, None)
            rows.append(row)

        return rows

    def extract_test_data(self, data):
        angles = []
        path = data['path']
        path_used = []
        road_distance = 0
        pivot_offs = []
        points = {}
        l_turns = 0
        r_turns = 0
        straight = 0
        road_distance = 0
        num_oobs = data['execution']['oobs']
        # road_test = RoadTest.from_dict(data)
        # dis = RoadTest.get_suite_coverage([road_test], 2)
        for seg_id in path:
            seg = data['network']['nodes'][str(seg_id)]
            if seg['roadtype'] == 'r_turn':
                r_turns += 1
            elif seg['roadtype'] == 'l_turn':
                l_turns += 1
            elif seg['roadtype'] == 'straight':
                straight += 1

            if seg['angle'] < 0:
                seg['angle'] += 360

            if seg['angle'] > 0:
                angles.append(seg['angle'])

            if seg['pivot_off'] > 0:
                pivot_offs.append(seg['pivot_off'])        

            points[seg_id] = Point(seg['x'], seg['y'])
            path_used.append(seg_id)
            
            if seg['key'] in data['execution']['seg_oob_count'].keys(): #fix is seg in oob
                num_oobs += -1
        if not pivot_offs:
            pivot_offs.append(0)    

        for i in range(0, len(path_used)-1):
            road_distance += self.get_distance(points[path_used[i]], points[path_used[i+1]])
        # direct_distance = self.get_distance(Point(data['start'][0], data['start'][1]), Point(data['goal'][0], data['goal'][1]))
        direct_distance = self.get_distance(points[path_used[0]], points[path_used[-1]])
        # max_distance = data['execution']['maximum_distance']
        # avg_distance = data['execution']['average_distance']

        # if data['execution']['oobs'] > 0 and max_distance >= 3:
        if data['execution']['oobs'] > 0:
            safety = 'unsafe'
        else:
            safety = 'safe'
        
        result = {
            'direct_distance': direct_distance,
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


    def transform_to_row_data(self, directory, outputfile, ai_type='beamng'): 
        '''
        creates a csv file out of json files from beamng data
        '''
        file_pairs = self.search_files(directory)
        counter = 0
        # outputfile = '{}/{}'.format(self.output_folder, outputfile)
        outputfile = '{}_{}'.format(ai_type, outputfile)
        with open(outputfile, 'w', newline='') as csv_file:
            fieldnames = ['is_start_seg', 'is_last_seg','prev_is_right_turn', 'prev_is_left_turn', 'prev_is_straight', 'prev_angles', 'prev_pivot_off', 'prev_actual_length','prev_direct_length', 'prev_directed_hausdorff',
            'seg_is_right_turn', 'seg_is_left_turn', 'seg_is_straight','seg_angles', 'seg_pivot_off', 'seg_actual_length','seg_direct_length', 
            'next_is_right_turn', 'next_is_left_turn', 'next_is_straight', 'next_angles', 'next_pivot_off', 'next_actual_length','next_direct_length', 'next_directed_hausdorff',
            'safety']
            # fieldnames = ['is_start_seg', 'is_last_seg','prev_is_right_turn', 'prev_is_left_turn', 'prev_is_straight', 'prev_angles', 'prev_pivot_off', 'prev_actual_length','prev_direct_length',
            # 'seg_is_right_turn', 'seg_is_left_turn', 'seg_is_straight','seg_angles', 'seg_pivot_off', 'seg_actual_length','seg_direct_length', 
            # 'next_is_right_turn', 'next_is_left_turn', 'next_is_straight', 'next_angles', 'next_pivot_off', 'next_actual_length','next_direct_length',
            # 'safety']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()          
            for filename, file_paths in file_pairs[ai_type].items():
                with open(file_paths['exec_file']) as json_file:
                    try:
                        data = json.load(json_file)
                        if not 'execution' in data.keys():
                            continue
                        rows = self.extract_segment_features_rows(data)
                        print('file: {}'.format(counter))
                        counter += 1
                        for row in rows:
                            writer.writerow(row)
                    except Exception as e:
                        print(e)
            
        return outputfile


    def extract_segment_features_rows(self, data):
        rows = []
        num_oobs = data['execution']['oobs']
        path = data['path']
        stop_at_last_oob = True
        if data['execution']['reason'] == 'goal_reached':
            stop_at_last_oob = False

        for i in range(0, len(path)):
           
            row = {
                'is_start_seg': 0,
                'is_last_seg': 0,
            }
            seg_id = path[i]
            seg = data['network']['nodes'][str(seg_id)]
            prev_seg = next_seg = None
            if i == 0:
                row['is_start_seg'] = 1
            else:
                prev_seg = data['network']['nodes'][str(path[i-1])]
            if i == len(path)-1:
                row['is_last_seg'] = 1
            else:
                next_seg = data['network']['nodes'][str(path[i+1])]
            row.update(self.segment_to_feature(seg, prev_seg, next_seg))
            if seg['key'] in data['execution']['seg_oob_count'].keys(): #fix is seg in oob
                row['safety'] = 'unsafe'
                num_oobs += -1
            else:
                row['safety'] = 'safe'
            rows.append(row)
            if num_oobs == 0 and stop_at_last_oob:
                break
        return rows

    def segment_to_feature(self,segment, prev_seg={}, next_seg={}):
        prev_seg_feature = next_seg_feature = {}
        seg_l_lane =  np.array([(p[0], p[1]) for p in segment['l_lanes'][0]['l_edge']])
        if prev_seg:
            prev_seg_feature = self.segment_extract_feature(prev_seg, 'prev')
            prev_l_lane = np.array([(p[0], p[1]) for p in prev_seg['l_lanes'][0]['l_edge']])
            prev_seg_feature['prev_directed_hausdorff'] = directed_hausdorff(seg_l_lane, prev_l_lane)[0]

        else:
            prev_seg_feature = {
            'prev_angles': -1,
            'prev_is_right_turn': 0,
            'prev_is_left_turn': 0,
            'prev_is_straight': 0,
            'prev_pivot_off': -1,
            'prev_actual_length': -1,
            'prev_direct_length': -1,
            'prev_directed_hausdorff': -1
        }
        if next_seg:
            next_seg_feature = self.segment_extract_feature(next_seg, 'next')
            next_seg_l_lane =  np.array([(p[0], p[1]) for p in next_seg['l_lanes'][0]['l_edge']])
            next_seg_feature['next_directed_hausdorff'] = directed_hausdorff(seg_l_lane, next_seg_l_lane)[0]


        else:
            next_seg_feature = {
            'next_angles': -1,
            'next_is_right_turn': 0,
            'next_is_left_turn': 0,
            'next_is_straight': 0,
            'next_pivot_off': -1,
            'next_actual_length': -1,
            'next_direct_length': -1,
            'next_directed_hausdorff': -1

        }
        seg_feature = self.segment_extract_feature(segment, 'seg')
        result = {**seg_feature, **prev_seg_feature, **next_seg_feature}
        return result

    def segment_extract_feature(self, segment, prefix):
        l_lane = [Point(p[0], p[1]) for p in segment['l_lanes'][0]['l_edge']]
        r_lane = [Point(point[0], point[1]) for point in segment['r_lanes'][0]['r_edge']]

        l_lane_distance = sum([self.get_distance(x,y) for x,y in zip(l_lane[:-1], l_lane[1:])]) 
        r_lane_distance = sum([self.get_distance(x,y) for x,y in zip(r_lane[:-1], r_lane[1:])])
        direct_distance = (self.get_distance(l_lane[0], l_lane[-1]) + self.get_distance(r_lane[0], r_lane[-1])) / 2
        is_right_turn = is_left_turn = is_straight = 0
        if segment['roadtype'] == 'l_turn':
            is_left_turn = 1
        elif segment['roadtype'] == 'r_turn':
            is_right_turn = 1
        elif segment['roadtype'] == 'straight':
            is_straight = 1

        segment_feature = {
            '{}_angles'.format(prefix): segment['angle'],
            '{}_is_right_turn'.format(prefix): is_right_turn,
            '{}_is_left_turn'.format(prefix): is_left_turn,
            '{}_is_straight'.format(prefix): is_straight,
            '{}_pivot_off'.format(prefix): segment['pivot_off'],
            '{}_actual_length'.format(prefix): (r_lane_distance+l_lane_distance)/2,
            '{}_direct_length'.format(prefix): direct_distance
        }
        return segment_feature


    def test_performance(self, training_dir, test_dir, use_models=[], num_tests=10, rounds=10, output='performace_result.json'):
        result = {
            'random_fix': None,
            'random_reach': None,
            'model_fix': None,
            'model_reach': None
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            self.temp_dir = temp_dir
            data_file = '{}/{}'.format(self.temp_dir, 'data_set.csv')
            tests = ['{}/{}'.format(test_dir, f) for f in os.listdir(test_dir) if os.path.isfile(os.path.join(test_dir, f))]
            result['random_fix'] = self.get_random_baseline_fixed_test_num(tests, num_tests, rounds)
            result['random_reach'] = self.get_random_baseline_reach_unsafe_num(tests, num_tests, rounds)
            data_file = self.transform_to_test_data(training_dir, data_file, 'beamng')
            training_file = self.create_training_test(data_file, self.temp_dir.name)
            # models  = self.build_models(training_file, temp_dir)
            # result['model_fix'] = self.model_based_fixed_baseline(tests, num_tests, rounds, models)
            # result['model_reach'] = self.get_model_baseline_reach_unsafe_num(tests, num_tests, rounds, models)
            with open(output, 'w') as outfile:
                outfile.write(json.dumps(result, sort_keys=True, indent=4))
            return output


    def build_models(self, trainings_file, temp_dir):
        models = ['J48.model', 'RandomForest.model', 'Logistic.model']
        #  'Logistic.model', 'RandomForest.model'
        p = subprocess.call(['java', '-jar', MODEL_BUILDING_JAR, trainings_file, temp_dir])

        return ['{}/{}'.format(temp_dir, model) for model in models]

    def get_random_baseline_fixed_test_num(self, test_set, num_tests, rounds):
        result = []
        avg_result = {
            'avg_total_costs': 0,
            'avg_cost_safe': 0,
            'avg_num_unsafe':0,
            'avg_num_safe': 0,
            'avg_cost_unsafe': 0,
            'avg_num_tests': 0
        }
        for i in range(0, rounds):
            test_files = self.random_test_selection(test_set, num_tests)
            result.append(self.evaluate_tests(test_files))
            print('Random_fixed. round: {}'.format(i))

        for res in result:
            avg_result['avg_total_costs'] += res['total_cost'] / len(result)
            avg_result['avg_cost_safe'] += res['cost_safe'] / len(result)
            avg_result['avg_num_unsafe'] += res['num_unsafe'] / len(result)
            avg_result['avg_num_safe'] += res['num_safe'] / len(result)
            avg_result['avg_cost_unsafe'] += res['cost_unsafe'] / len(result)
            avg_result['avg_num_tests'] += res['num_tests'] / len(result)
        
        avg_result['results'] = result

        return avg_result

    def get_random_baseline_reach_unsafe_num(self, test_set, num_unsafe, rounds):
        result = []
        for i in range(0, rounds):
            print('Random_reached. round: {}'.format(i))
            avg_result = {
                'avg_total_costs': 0,
                'avg_cost_safe': 0,
                'avg_num_unsafe':0,
                'avg_cost_unsafe': 0,
                'avg_num_safe': 0,
                'avg_num_tests': 0
            }
            count_unsafe = 0
            test_files = []
            max_index = len(test_set)-1
            while(count_unsafe < num_unsafe):
                test = test_set[random.randint(0, max_index)]
                test_files.append(test)
                with open(test) as json_file:
                    data = json.load(json_file)
                    if data['execution']['oobs'] > 0:
                        count_unsafe += 1
            result.append(self.evaluate_tests(test_files))
        
        for res in result:
            avg_result['avg_total_costs'] += res['total_cost'] / len(result)
            avg_result['avg_cost_safe'] += res['cost_safe'] / len(result)
            avg_result['avg_num_unsafe'] += res['num_unsafe'] / len(result)
            avg_result['avg_num_safe'] += res['num_safe'] / len(result)
            avg_result['avg_cost_unsafe'] += res['cost_unsafe'] / len(result)
            avg_result['avg_num_tests'] += res['num_tests'] / len(result)

        avg_result['results'] = result

        return avg_result

    def random_test_selection(self, tests=[], num_tests=10):
        random_selected_tests = []
        sampled_test = 0
        while sampled_test < num_tests:
            random_num = random.randint(0, (len(tests)-1))
            if tests[random_num] not in random_selected_tests:
                random_selected_tests.append(tests[random_num])
                sampled_test += 1
        return random_selected_tests

    def convert_to_test(self, test, exclude_features=[]):
        to_test = tempfile.NamedTemporaryFile(delete=False)
        fieldnames = ['direct_distance', 'road_distance', 'num_l_turns','num_r_turns','num_straights','median_angle','total_angle','mean_angle','std_angle',
        'max_angle','min_angle','median_pivot_off','mean_pivot_off','std_pivot_off','max_pivot_off','min_pivot_off', 'safety']
        for feature in exclude_features:
            fieldnames.pop(feature, None)

        with open(to_test.name, 'w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()          
            features = self.extract_features_for_test_case(test, exclude_features)
            # writer.writerow(features)
            features['safety'] = 'safe'
            writer.writerow(features)
            features['safety'] = 'unsafe'
            writer.writerow(features)

        return to_test.name

    def make_prediction(self, model, to_test):
        try:
            csv_name = '{}.csv'.format(to_test)
            csv_file = copyfile(to_test, csv_name)
            process = subprocess.Popen(['java', '-jar', PREDICTION_JAR, csv_file, model], stdout=subprocess.PIPE)
            safe_pattern = '.*0.0'
            unsafe_pattern = '.*1.0'
            output = process.stdout.readline()
            output = str(output.strip())
            if re.search(safe_pattern, output):
                result = 'safe'
            elif re.search(unsafe_pattern, output):
                result = 'unsafe'
            print('Result: {}'.format(output))
            return result
        except Exception as e:
            print(e)

    def evaluate_tests(self, tests):
        result = {
            'total_cost': 0,
            'cost_safe': 0,
            'cost_unsafe': 0,
            'num_unsafe':0,
            'num_safe': 0
        }
        for test in tests:
            with open(test) as json_file:
                data = json.load(json_file)
                execution_time = (datetime.strptime(data['execution']['end_time'], '%Y-%m-%dT%H:%M:%S.%f') - datetime.strptime(data['execution']['start_time'], '%Y-%m-%dT%H:%M:%S.%f')).total_seconds()
                if data['execution']['oobs'] > 0:
                    result['num_unsafe'] += 1
                    result['cost_unsafe'] += execution_time

                else:
                    result['cost_safe'] += execution_time
                    result['num_safe'] += 1
                result['total_cost'] += execution_time
        result['num_tests'] = result['num_safe'] + result['num_unsafe']
        return result

    def evaluate_test(self, test):
        result = {
            'cost': 0,
            'is_safe': True,
        }
        with open(test) as json_file:
            data = json.load(json_file)
            execution_time = (datetime.strptime(data['execution']['end_time'], '%Y-%m-%dT%H:%M:%S.%f') - datetime.strptime(data['execution']['start_time'], '%Y-%m-%dT%H:%M:%S.%f')).total_seconds()
            if data['execution']['oobs'] > 0:
                result['is_safe'] = False
            result['cost'] += execution_time
        return result


    def model_based_fixed_baseline(self, test_set, num_tests, rounds, models=[]):
        model_to_result = {}
        for model in models:
            avg_result = {
                'avg_total_costs': 0,
                'avg_saved_costs': 0,
                'avg_cost_from_safe_file':0,
                'avg_num_unsafe_file_tested': 0,
                'avg_num_missed_unsafe_tests': 0,
                'avg_num_safe_file_tested': 0,
                'avg_num_missed_safe_tests': 0
            }
            results = []
            for i in range(0, rounds):
                print('Model_fixed. round: {}'.format(i))
                results.append(self.round_model_performance_test(test_set, num_tests, model))
            for res in results:
                avg_result['avg_total_costs'] += res['total_costs'] / len(results)
                avg_result['avg_num_missed_unsafe_tests'] += res['num_missed_unsafe_tests'] / len(results)
                avg_result['avg_num_safe_file_tested'] += res['num_safe_file_tested'] / len(results)
                avg_result['avg_cost_from_safe_file'] += res['cost_from_safe_file'] / len(results)
                avg_result['avg_num_unsafe_file_tested'] += res['num_unsafe_file_tested'] / len(results)
                avg_result['avg_saved_costs'] += res['saved_costs'] / len(results)
                avg_result['avg_num_missed_safe_tests'] += res['num_missed_safe_tests'] / len(results)

            avg_result['results'] = results


            model_to_result[model] = avg_result

        return model_to_result

    def round_model_performance_test(self, test_set, num_tests, model):
        result = {
                'num_missed_unsafe_tests': 0,
                'num_missed_safe_tests': 0,
                'saved_costs': 0,
                'total_costs': 0,
                'num_safe_file_tested': 0,
                'num_unsafe_file_tested': 0,
                'cost_from_safe_file': 0
            }
        tested_files = 0
        already_tested_files = []
        while tested_files < num_tests:
            while True:
                file = self.random_test_selection(test_set, 1)[0]
                if file not in already_tested_files:
                    already_tested_files.append(file)
                    break
            test_file = self.convert_to_test(file)
            safety_prediction = self.make_prediction(model, test_file)
            os.remove(test_file)

            ev = self.evaluate_test(file)
            if safety_prediction == 'safe':
                if ev['is_safe']:
                    result['saved_costs'] += ev['cost']
                    result['num_missed_safe_tests'] += 1
                else:
                    result['num_missed_unsafe_tests'] += 1

            elif safety_prediction == 'unsafe':
                tested_files += 1
                if ev['is_safe']:
                    result['cost_from_safe_file'] += ev['cost']
                    result['num_safe_file_tested'] += 1
                else:
                    result['num_unsafe_file_tested'] += 1
                result['total_costs'] += ev['cost']
        return result


    def get_model_baseline_reach_unsafe_num(self, test_set, num_unsafe, rounds, models):
        model_to_result = {}
        for model in models:
            avg_result = {
                'avg_total_costs': 0,
                'avg_saved_costs': 0,
                'avg_cost_from_safe_file':0,
                'avg_num_unsafe_file_tested': 0,
                'avg_num_missed_unsafe_tests': 0,
                'avg_num_safe_file_tested': 0,
                'avg_num_missed_safe_tests': 0
            }
            results = []
            for i in range(0, rounds):
                print('Model_reached. round: {}'.format(i))
                count_unsafe = 0
                test_files = []
                max_index = len(test_set)-1
                result = {
                    'num_missed_unsafe_tests': 0,
                    'num_missed_safe_tests': 0,
                    'saved_costs': 0,
                    'total_costs': 0,
                    'num_safe_file_tested': 0,
                    'num_unsafe_file_tested': 0,
                    'cost_from_safe_file': 0
                }
                while(count_unsafe < num_unsafe):
                    while True:
                        test = test_set[random.randint(0, max_index)]
                        if test not in test_files:
                            test_files.append(test)
                            break

                    test_file = self.convert_to_test(test)

                    safety_prediction = self.make_prediction(model, test_file)
                    os.remove(test_file)

                    ev = self.evaluate_test(test)
                    if safety_prediction == 'safe':
                        if ev['is_safe']:
                            result['saved_costs'] += ev['cost']
                            result['num_missed_safe_tests'] += 1
                        else:
                            result['num_missed_unsafe_tests'] += 1

                    elif safety_prediction == 'unsafe':
                        if ev['is_safe']:
                            result['cost_from_safe_file'] += ev['cost']
                            result['num_safe_file_tested'] += 1
                        else:
                            result['num_unsafe_file_tested'] += 1
                            count_unsafe += 1
                        result['total_costs'] += ev['cost']

                results.append(result)
            
            for res in results:
                avg_result['avg_total_costs'] += res['total_costs'] / len(results)
                avg_result['avg_num_missed_unsafe_tests'] += res['num_missed_unsafe_tests'] / len(results)
                avg_result['avg_num_safe_file_tested'] += res['num_safe_file_tested'] / len(results)
                avg_result['avg_cost_from_safe_file'] += res['cost_from_safe_file'] / len(results)
                avg_result['avg_num_unsafe_file_tested'] += res['num_unsafe_file_tested'] / len(results)
                avg_result['avg_saved_costs'] += res['saved_costs'] / len(results)
                avg_result['avg_num_missed_safe_tests'] += res['num_missed_safe_tests'] / len(results)

            avg_result['results'] = results

            model_to_result[model] = avg_result

        return model_to_result


    def create_training_test(self, data_set, output_folder):
        df = pd.read_csv(data_set)
        df['safety'] = df['safety'].map(self.label_map)

        is_safe = df['safety'] == 1
        not_safe = df['safety'] == 0

        df_safe = df[is_safe]
        df_not_safe = df[not_safe]
        num_not_safe = int(len(df_not_safe))
        num_safe = int(len(df_safe))
        if num_safe >= num_not_safe:
            num_sample = num_not_safe
            remaining_num = len(df_not_safe) - num_sample
        else:
            num_sample = num_safe
            remaining_num = len(df_safe) - num_sample

        sample_safe = df_safe.sample(n=num_sample, random_state=1)
        sample_unsafe = df_not_safe.sample(n=num_sample, random_state=1)

        training_set = pd.concat([sample_safe, sample_unsafe])

        # if should_normalize:
        #     training_set = self.min_max_normalize(training_set)
        #     test_set = self.min_max_normalize(test_set)
        #     balanced_set = self.min_max_normalize(balanced_set)

        training_set['safety'] = training_set['safety'].map(self.reverse_label_map)
        training_path = '{}/training.csv'.format(output_folder)
        


        training_set.to_csv(training_path, index=False)
       


        # pandas2arff(training_set, training_path_arff, cleanstringdata=True, cleannan=True)
        # pandas2arff(test_set, test_path_arff, cleanstringdata=True, cleannan=True)
        # pandas2arff(balanced_set, test_balanced_path_arff, cleanstringdata=True, cleannan=True)

        return training_path
    
    def split_data(self, safe_dir, unsafe_dir, out_dir, train_test_ratio, unsafe_ratio):
        counter = 0
        safe_files = ['{}/{}'.format(safe_dir, f) for f in listdir(safe_dir) if isfile(join(safe_dir, f))]
        unsafe_files = ['{}/{}'.format(unsafe_dir, f) for f in listdir(unsafe_dir) if isfile(join(unsafe_dir, f))]

        if len(safe_files) < len(unsafe_files):
            num_to_sample = int(train_test_ratio * len(safe_files))
        else:
            num_to_sample = int(train_test_ratio * len(unsafe_files))

        training_dir = os.mkdir('{}/training'.format(out_dir))
        test_dir = os.mkdir('{}/test'.format(out_dir))
        safe_training = random.sample(safe_files, num_to_sample)
        for safe_sample in safe_training:
            safe_files.remove(safe_sample)
        unsafe_training  = random.sample(safe_files, num_to_sample)
        for unsafe_sample in unsafe_training:
            unsafe_files.remove(unsafe_sample)
        training_set = safe_training + unsafe_training
        
        if len(safe_files) * (1-unsafe_ratio) < len(unsafe_files) * unsafe_ratio:
            num_unsafe_sample = int(unsafe_ratio * len(unsafe_files))
            num_safe_sample =  int(unsafe_ratio * len(safe_files))
        else:
            num_unsafe_sample = int(unsafe_ratio * len(unsafe_files))
            num_safe_sample = int(unsafe_ratio * len(safe_files))
        safe_test = random.sample(safe_files,num_unsafe_sample)
        unsafe_test = random.sample(unsafe_files,num_safe_sample)
        test_set = safe_test + unsafe_test
        for training in training_set:
            filename = training.split('/')[-1]
            copyfile(training, '{}/{}'.format(out_dir, filename))
        for test in test_set:
            filename = training.split('/')[-1]
            copyfile(test, '{}/{}'.format(out_dir, filename))

        return training_dir.name, test_dir.name


if __name__ == '__main__':
    # directory = 'D:/master thesis/DataSet/execs/beamng_risk_1_5'
    # directory = 'C:/Users/bboss/.asfaultenv/output/replay'
    data_set_generator = DataSetGenerator()
  
    # # data_set = data_set_generator.transform_to_test_data(directory, sys.argv[1], 'deepdrive')
    # # new_dir = data_set_generator.create_training_test_set(data_set, float(sys.argv[2]))
    # # shutil.move(data_set, '{}/{}'.format(new_dir, sys.argv[1]))
  
    # directory = 'D:/MasterThesis/DataSet/beamng'
    # data_set = data_set_generator.transform_to_test_data(directory, sys.argv[1], 'default')
    # data_set = data_set_generator.transform_to_row_data(directory, sys.argv[1], 'beamng')
    # print('Split dataset')
    # new_dir, training_set, test_set, balanced_set = data_set_generator.create_training_test_set(data_set, float(sys.argv[2]), False)
    # shutil.move(data_set, '{}/{}'.format(new_dir, sys.argv[1]))
   
    # result_path ='C:/workspace/MasterThesis/datasets/result_v3.csv'
    # print('start weka')
    # subprocess.call(['java', '-jar', './scripts/jars/weka_pip_updated.jar', training_set, test_set, balanced_set, sys.argv[1],result_path])
    
    
    '''
    splitting training/test set
    training_dir = 'D:/MasterThesis/Dataset/performance_test/training'
    test_dir = 'D:/MasterThesis/Dataset/performance_test/test'
    data_set_generator.test_performance(training_dir, test_dir)
    '''
  
  
  
  
  
  
    test_dir = 'D:/MasterThesis/Dataset/performance_test/beamng/test'
    training_dir = 'D:/MasterThesis/Dataset/performance_test/beamng/training'
    # # model = 'C:/workspace/MasterThesis/datasets/datasetsclass_weka.classifiers.trees.J48'
    # # to_test ='C:/workspace/MasterThesis/datasets/to_test.csv'
    # # tests = [os.path.join(test_dir, f) for f in os.listdir(test_dir) if os.path.isfile(os.path.join(test_dir, f))]
    # # result = data_set_generator.model_based_fixed_baseline(tests, 100, 1, models=[model])
    # data_set = data_set_generator.transform_to_test_data(training_dir, 'test_prediction.csv', 'beamng')
    result = data_set_generator.test_performance(training_dir=training_dir, test_dir=test_dir, use_models=[], num_tests=10, rounds=100, output='random_baseline.json')
    print(result)