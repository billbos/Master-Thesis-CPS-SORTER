"""This file starts DriveBuild created files locally in BeamNG and calculates
   the elapsed time and the cumulative distance to the center of the road.
   WARNING: You don't have to use this file when DriveBuild works for you.
"""

from beamngpy import BeamNGpy, Scenario, Vehicle
from pathlib import Path
from os import path, listdir
from glob import glob
from shutil import copy
from shapely.geometry import LineString
from shapely.geometry import Point
import time
from test_subjects.deepjanus import DeepJanus
from termcolor import colored

REFRESH_RATE = 60
STEPS_WITHOUT_CONTROL = 6


def start_test(control_points, deterministic=False):
    """Starts DriveBuild creates files locally and moves them to the trunk folder.
    :param control_points: List of control points without width.
    :param deterministic: {@code True} if AI is deterministic.
    :return: Tuple of cumulative distance and time.
    """
    line = LineString(control_points)
    bng = BeamNGpy('localhost', 64256)

    vehicle = Vehicle('ego', model='etk800', licence='PYTHON')

    subject = DeepJanus(vehicle, bng)

    # TODO Change path to where DriveBuild creates folders and BeamNG files (path should already exist).
    # Don't select a specific DriveBuild directory.
    src_dir = "C:\\Users\\Alessio\\beamng-research_unlimited\\trunk\\levels"
    matches = glob(src_dir + "\\drivebuild*")
    latest_time = 0

    # Fetches the latest created DriveBuild directory.
    for folder in matches:
        if latest_time < path.getmtime(folder):
            latest_time = path.getmtime(folder)
            src_dir = folder
    src_dir = src_dir + "\\levels\\drivebuild\\scenarios"
    file_list = listdir(src_dir)
    target_file = ""
    latest_time = 0

    # Fetches the latest created files.
    for file in file_list:
        tmp_file = src_dir + "\\" + file
        if latest_time < path.getmtime(tmp_file):
            latest_time = path.getmtime(tmp_file)
            target_file = file
    target_file = target_file.split('.')[0]
    scenario = Scenario('drivebuild', target_file)
    scenario.add_vehicle(vehicle, pos=(-0, 0, 0), rot=(0, 0, 0))

    # TODO Change path to your trunk folder and choose a custom folder for DriveBuild files in levels.
    # If it is a new one, consider to create a 'scenarios' folder. If you get texture issues,
    # then you didn't link to the drivebuild directory. You can also copy the textures to this folder.
    # Copies the files from the document directory to the trunk levels directory.
    destination_path = 'D:\\Program Files (x86)\\BeamNG\\levels\\drivebuild\\scenarios'
    scenario.path = Path(destination_path)
    for file in file_list:
        copy(src_dir + "\\" + file, destination_path)

    print(colored("Calculating fitness value...", "blue"))
    time.sleep(4)

    bng.open()
    bng.load_scenario(scenario)
    bng.start_scenario()
    # vehicle.ai_set_mode('span')
    # vehicle.ai_set_speed('40')
    # vehicle.ai_drive_in_lane(True)
    if deterministic:
        bng.set_steps_per_second(REFRESH_RATE)
        bng.set_deterministic()
    else:
        # Start the test subject in a new thread.
        subject.start()

    distance = 0
    start = time.time()
    for _ in range(240):
        time.sleep(0.5)
        if vehicle.state is not None:
            if deterministic:
                subject.step()
                bng.step(STEPS_WITHOUT_CONTROL)
            # Current position of the car.
            # vehicle.update_vehicle()
            x, y, _ = vehicle.state["pos"]
            car_pos = Point(x, y)
            if (abs(x - control_points[-1][0]) < 7 and abs(y - control_points[-1][1]) < 7) \
                    or (time.time() - start >= 80):
                subject.stop()
                # beautiful solution to make sure
                # that bng is not called by the test subject during close()
                time.sleep(1)
                bng.close()
                elapsed_time = time.time() - start
                return [distance, elapsed_time]
            else:
                dist = car_pos.distance(line)
                distance += dist
