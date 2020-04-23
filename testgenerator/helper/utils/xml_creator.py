"""This file offers methods to create xml files of a list of control points.
  Methods are preconfigured to meet the requirements of the road_generator.py
  class.
"""

from .dbe_xml_builder import DBEBuilder
from .dbc_xml_builder import DBCBuilder


def build_environment_xml(control_points, file_name="exampleTest"):
    """Creates a dbe xml file.
    :param control_points: List of control points as tuples.
    :param file_name: Name of this dbe file.
    """
    dbe = DBEBuilder()
    dbe.add_lane(control_points)
    dbe.save_xml(file_name)


def build_criteria_xml(snd_point, car, file_name="exampleTest", env_name="exampleTest",
                       name="Example Test", fps="60", frequency="6", car_id="ego"):
    """Creates a dbc xml file. Failure, success and preconditions are controlled
      manually for this test generation since the road_generator creates simple
      lane following tests.
    :param snd_point: Second point of the control point list, needed for precondition.
    :param car: List of car states. See build_xml method for more details.
    :param file_name: Name of this file.
    :param env_name: Name of the environment file without extensions.
    :param name: Self defined description name of this file.
    :param fps: frames per second
    :param frequency: Frequency of the AI to compute the next step.
    :param car_id: Unique identifier for the participant car.
    :return: Void.
    """
    dbc = DBCBuilder()
    dbc.define_name(name)
    dbc.environment_name(env_name)
    dbc.steps_per_second(fps)
    dbc.ai_freq(frequency)

    dbc.add_car(car[0], car[1])
    vc_pos = [car_id, snd_point[0], snd_point[1], 4]
    sc_speed = [car_id, 15]

    dbc.add_precond_partic_sc_speed(vc_pos, sc_speed)
    dbc.add_success_point([car_id, car[1][-1][0], car[1][-1][1], car[1][-1][2]])
    dbc.add_failure_conditions(car_id, "offroad")
    dbc.save_xml(file_name)


def _add_width(control_points, width):
    """Adds the width parameter for the whole list of control points.
    :param control_points: List of control points.
    :return: List of control points with the width parameter added.
    """
    new_list = []
    iterator = 0
    while iterator < len(control_points):
        new_list.append([control_points[iterator][0], control_points[iterator][1], width])
        iterator += 1
    return new_list


def build_xml(control_points, name, width):
    """Builds an environment and criteria xml file out of a list of control points.
    :param width: Desired width of each road segment.
    :param control_points: List of control points as tuples.
    :param name: Name of this file.
    :return: Void.
    """
    temp_list = _add_width(control_points, width)
    build_environment_xml(temp_list, name)

    init_state = [temp_list[0][0] + 3, temp_list[0][1], 0, "AUTONOMOUS", 50]

    waypoints = []

    # Comment this block in to add waypoints for every point in the list, e.g. for beamng ai.
    """
    waypoint = temp_list.pop(0)
    waypoint = [waypoint[0] + 3, waypoint[1], 4, "AUTONOMOUS"]
    waypoints.append(waypoint)
    if len(temp_list) > 20:
        for x in range(0, 5):
            temp_list.pop(0)
    for point in temp_list:
        waypoint = [point[0], point[1], 4, "AUTONOMOUS"]
        waypoints.append(waypoint)
    """
    waypoints.append([temp_list[-1][0], temp_list[-1][1], 4, "AUTONOMOUS"])
    car = [init_state, waypoints]
    build_criteria_xml(temp_list[0], car, name, name)


def build_all_xml(population, width, files_name="exampleXML"):
    """Calls the build_xml method for each individual.
    :param width: Desired width of each road segment.
    :param population: List of individuals containing control points and a fitness value for each one.
    :param files_name: Name of this file.
    :return: Void.
    """
    iterator = 0
    while iterator < len(population):
        file_name = files_name + str(iterator)
        build_xml(population[iterator][0], file_name, width)
        iterator += 1
