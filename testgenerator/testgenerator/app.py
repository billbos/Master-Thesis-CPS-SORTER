import datetime
from testgenerator.services.weka_helper import WekaHelper
from testgenerator.services.road_transformer import RoadTransformer
from asfault import config, experiments
from asfault.beamer import *
from asfault.network import *
from asfault.evolver import *
from asfault.graphing import *
from asfault.plotter import *
from deap import base, creator, tools
from subprocess import Popen
import tempfile
import csv
import pandas as pd
import numpy as np
import os

DEFAULT_LOG = 'asfault.log'
DEFAULT_ENV = os.path.join(str(Path.home()), '.asfaultenv')

def log_exception(extype, value, trace):
    l.exception('Uncaught exception:', exc_info=(extype, value, trace))


def setup_logging(log_file):
    file_handler = l.FileHandler(log_file, 'a', 'utf-8')
    term_handler = l.StreamHandler()
    l.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                  level=l.INFO, handlers=[term_handler, file_handler])
    sys.excepthook = log_exception
    l.info('Started the logging framework writing to file: %s', log_file)



class Testgenerator:
    def __init__(self, temp_dir=None, weka_helper=None, output_dir=None):
        setup_logging(DEFAULT_LOG)
        ensure_environment(DEFAULT_ENV)
        generate_factories()
        config.ex.ai_controlled = 'true'
        if not temp_dir:
            temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = output_dir
        self.temp_dir = temp_dir
        self.test_dir = os.mkdir(os.path.join(self.temp_dir.name, 'test_files'))
        self.weka_helper = weka_helper
        self.road_transformer = RoadTransformer()
        self.runner_factory = gen_beamng_runner_factory(config.ex.get_level_dir(), config.ex.host, config.ex.port, plot=False)



    def generate_tests(self, time_budget, weka_model):
        self.log_file = open('{}/log_file.txt'.format(self.output_dir), 'w')
        counter = 0
        results = {
            'generated_tests': 0,
            'tested_files': 0,
            'unsafe_cases': 0,
            'safe_cases': 0,
            'predicated_as_safe': 0
        }
        test_factory = RoadTestFactory(config.ev.bounds)

        start_time = datetime.datetime.now()
        self.log_file.write('Start Time: {} \n'.format(start_time))
        end_time = start_time + datetime.timedelta(minutes=time_budget)
        print('Start time: {}'.format(start_time))
        
        while datetime.datetime.now() < end_time:
            to_predict, test_case = self.generate_test_case(test_factory)           
            # test_file = tempfile.NamedTemporaryFile(delete=False)
            prediction = self.weka_helper.make_prediction(weka_model, to_predict)
            results['generated_tests'] += 1
            if prediction == 'unsafe':
                results['tested_files'] += 1
                test_case.execution = self.run_test(test_case)
                res = self.evaluate_test_case(test_case)
                if res == 'safe':
                    results['safe_cases'] += 1
                    self.log_file.write('{}: Mistaken Safe Test Case for Unsafe num: {} \n'.format(datetime.datetime.now(), results['safe_cases']))
                elif res == 'unsafe':
                    results['unsafe_cases'] += 1
                self.log_file.write('{}: Found Unsafe Test Case num: {} \n'.format(datetime.datetime.now(), results['unsafe_cases']))
                print('Generated: {} files'.format(results['tested_files']))
            else:
                # results['predicted_as_safe'].append(test_case)
                results['predicated_as_safe'] += 1

            with open('{}/test_{}.json'.format(self.output_dir, counter), 'w') as out:
                out.write(json.dumps(RoadTest.to_dict(test_case), sort_keys=True, indent=4))

            counter += 1
            if counter % 10 ==0:
                elapsed_time = datetime.datetime.now() - start_time
                print("::::::::::::Elapsed Time::::::::: {}".format(str(datetime.timedelta(seconds=elapsed_time.total_seconds()))))
                print("Tempresult: {}".format(results))

        self.log_file.write('End time: {}'.format(datetime.datetime.now()))


        print('End time: {}'.format(datetime.datetime.now()))
        print('Files: {}'.format(results['generated_tests']))
        return results

                
    def generate_test_case(self, factory):
        test = factory.generate_random_test()
        test_file = self.road_transformer.convert_to_test(RoadTest.to_dict(test))
        return test_file, test

   
    def get_distance(self, point_a, point_b):
        return np.sqrt( ((point_a.x-point_b.x)**2)+((point_a.y-point_b.y)**2))

  
    def evaluate_test_case(self, test_case):
        execution = test_case.execution
        if execution.oobs > 0 and execution.reason == 'off_track':
            return 'unsafe'
        else:
            return 'safe'


    def run_test(self, test):
        while True:
            # Test Runner is bound to the test. We need to configure the factory to return a new instance of a runner
            # configured to use the available BeamNG
            runner = self.runner_factory(test)
            try:
                execution = runner.run()
                return execution
            except Exception as e:
                l.error('Error running test %s', test)
                l.exception(e)
                sleep(30.0)
            finally:
                runner.close()

    def write_result_to(self, result, output):
        with open('{}/results.txt'.format(output), 'w') as outfile:
            json.dump(result, outfile)

def milliseconds():
    return round(time() * 1000)


def read_environment(env_dir):
    l.info('Starting with environment from: %s', env_dir)
    config.load_configuration(env_dir)


def ensure_environment(env_dir):
    if not os.path.exists(env_dir):
        l.info('Initialising empty environment: %s', env_dir)
        config.init_configuration(env_dir)
    read_environment(env_dir)


if __name__=='__main__':
    temp_dir = tempfile.TemporaryDirectory()
    output_dir = 'C:/Users/bboss/.asfaultenv/output/tests'
    # output_res = 'C:/Users/bboss/.asfaultenv/output/tests/result.txt '
    training_dir = 'D:/MasterThesis/Dataset/performance_test/beamng'
    data_file = '{}/data_file.csv'.format(temp_dir.name)
    road_tr = RoadTransformer()
    road_tr.transform_to_training_data(training_dir, data_file, 'beamng')
    trainings_file = road_tr.create_training_test(data_file, temp_dir.name)

    weka = WekaHelper()
    weka.build_models(trainings_file=trainings_file, temp_dir=temp_dir.name, models=['J48.model'])
    
    test_generator = Testgenerator(temp_dir=temp_dir, weka_helper=weka, output_dir=output_dir)
    result = test_generator.generate_tests(time_budget=300, weka_model='J48.model')
    test_generator.write_result_to(result, output_dir)
