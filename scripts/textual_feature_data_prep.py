import json
import os    
from os import listdir
from os.path import isfile, join
import pandas as pd
from shutil import copyfile
import random
from asfault.tests import RoadTest


def main(directory, output):
    counter = 0
    for subdir, dirs, files in os.walk(directory):
        for filename in files:
            splited_subdir = subdir.split('\\')
            dir_name = splited_subdir[-1]
            filepath = subdir + os.sep + filename
            with open(filepath) as json_file:
                try:
                    data = json.load(json_file)
                    if not 'execution' in data.keys():
                        continue
                    else:
                        if counter % 2 == 0:
                            dir = 'training'
                        else:
                            dir = 'test'
                        if data.pop('execution', {})['oobs'] > 0:
                            with open('{}/{}/test_{}.json'.format(output, dir, counter), 'w') as fp:
                                json.dump(data, fp)
                                fp.write("\n")

                        else:
                            with open('{}/{}/test_{}.json'.format(output, dir, counter), 'w') as fp:
                                json.dump(data, fp)
                                fp.write("\n")

                        counter += 1
                        print('counter {}'.format(counter))
                except Exception as e:
                    print(e)

def create_training_test_set(input_folder, output_folder):    
    counter = 0
    for subdir, dirs, files in os.walk(input_folder):
        for filename in files:
            splited_subdir = subdir.split('\\')
            dir_name = splited_subdir[-1]
            filepath = subdir + os.sep + filename
            try:
                with open(filepath) as json_file:
                    data = json.load(json_file)
                    execution = data.pop('execution', {})
                    if execution['reason'] == 'timeout':
                        continue
                    if execution['oobs'] > 0:
                        dir = 'unsafe'
                    else:
                        dir = 'safe'
                copyfile(filepath, '{}/{}/test_{}.json'.format(output, dir, counter))
                counter += 1
                print('counter {}'.format(counter))
            except Exception as e:
                print(e)


def clean_folder(replay_folder, folder_to_clean):
    files_to_clean = [f for f in listdir(folder_to_clean) if isfile(join(folder_to_clean, f))]
    replayed_files = [f for f in listdir(replay_folder) if isfile(join(replay_folder, f))]

    for file in files_to_clean:
        if file in replayed_files:
            os.remove(join(folder_to_clean,file))
            print('removed : {}'.format(file))


def check_replay(replay_folder, output_folder):
    counter = 0
    for subdir, dirs, files in os.walk(replay_folder):
        for c, filename in enumerate(files):
            splited_subdir = subdir.split('\\')
            dir_name = splited_subdir[-1]
            filepath = subdir + os.sep + filename
            with open(filepath) as json_file:
                try:
                    data = json.load(json_file)
                    execution = data.pop('execution', {})
                    if execution['oobs'] > 0 and len(execution.get('seg_oob_count').keys()) == 0:
                        with open('{}/{}'.format(output_folder, filename), 'w') as fp:
                            json.dump(data, fp)
                            fp.write("\n")
                        print('file: {}, counter: {}'.format(c, counter))
                        counter += 1
                except Exception as e:
                    print(e)

def remove_timeout(folder):
    counter = 0
    for subdir, dirs, files in os.walk(folder):
        for c, filename in enumerate(files):
            is_timeout = False
            splited_subdir = subdir.split('\\')
            dir_name = splited_subdir[-1]
            filepath = subdir + os.sep + filename
            with open(filepath) as json_file:
                try:
                    data = json.load(json_file)
                    execution = data.pop('execution', {})
                    if execution['reason'] == 'timeout':
                        is_timeout = True
                        counter += 1
                    
                    print('file: {}, counter: {}'.format(c, counter))
                
                except Exception as e:
                    print(e)
            if is_timeout:
                os.remove(filepath)
    print('counter:::: {}'.format(counter))

def count_safe_unsafe(folder):
    result = {'unsafe':0, 'safe':0, 'time_spent_unsafe':0, 'time_spent_safe':0}
    for subdir, dirs, files in os.walk(folder):
        counter = 0
        for c, filename in enumerate(files):
            is_timeout = False
            splited_subdir = subdir.split('\\')
            dir_name = splited_subdir[-1]
            filepath = subdir + os.sep + filename
            with open(filepath) as json_file:
                try:
                    data = json.load(json_file)
                    # print(data)
                    if not data.get('execution', None):
                        continue
                    test = RoadTest.from_dict(data)
                    execution = test.execution
                    if execution.reason == 'timeout':
                        continue
                    if execution.oobs > 0:
                        result['unsafe'] += 1
                        result['time_spent_unsafe'] += (execution.end_time - execution.start_time).total_seconds()
                    else:
                        result['safe'] += 1
                        result['time_spent_safe'] += (execution.end_time - execution.start_time).total_seconds()
                except Exception as e:
                    print(e)
            print(counter)
            counter += 1
    return result

def add_oracle(file):
    df = pd.read_csv(file)
    df['safety'] = df['safety'].astype('str')
    file_name = file.split('/')[-1]
    for index, row in df.iterrows():
        safe = row['file'].split('_')[-2]
        df.at[index, 'safety'] = safe
        df = df

    df = df.drop(columns=['file'])
    df.to_csv(file_name, index=False)


if __name__ == '__main__':
    directory = 'D:/MasterThesis/DataSet/execs/beamng_risk_1_5'
    output = 'D:/MasterThesis/Dataset/performance_test/beamng'
    replay_folder = 'C:/Users/bboss/.asfaultenv/output/replay'
    files_to_clean = 'D:/MasterThesis/Dataset/text_features/training/unsafe'
    # main(directory, output)
    # clean_folder(replay_folder, files_to_clean)
    # training_files = 'C:/workspace/MasterThesis/Java-WP-to-extract-textual-features/ML-pipeline/R-resources/R-scripts/documents-preprocessed/tdm_full_trainingSet_with_oracle_info.csv'
    # test_files = 'C:/workspace/MasterThesis/Java-WP-to-extract-textual-features/ML-pipeline/R-resources/R-scripts/documents-preprocessed/tdm_full_testSet_with_oracle_info.csv'

    # add_oracle(training_files)guet 
    # add_oracle(test_files)
    # potential_rerun_folder = 'D:/MasterThesis/Dataset/potential_rerun'
    # check_replay(replay_folder, potential_rerun_folder)
    # remove_timeout(replay_folder)
    # create_training_test_set(directory, output)
    directory_to_count = 'D:/MasterThesis/Results/Performance/Online/6h_logistic'
    result = count_safe_unsafe(directory_to_count)
    print(result)