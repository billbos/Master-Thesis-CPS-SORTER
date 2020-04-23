from glob import glob
from os import path
from pathlib import Path
from random import randint, random, sample
from copy import deepcopy
from operator import itemgetter
from typing import Optional, Tuple
from shutil import move

from drivebuildclient.AIExchangeService import AIExchangeService
from termcolor import colored

from testgenerator.helper.utils.xml_creator import build_all_xml, build_xml
from testgenerator.helper.utils.plotter import plot_all
from testgenerator.helper.utils.validity_checks import *
from testgenerator.helper.utils.utility_functions import convert_points_to_lines

from shapely.geometry import LineString
from shapely import affinity
import numpy as np
import scipy.interpolate as si


class TestGenerator:
    """This class generates roads using a genetic algorithm."""

    def __init__(self, difficulty="Easy"):
        """
        :param difficulty: Variable roads characteristics, depending on how
                           feasible the roads should be for the AI. Possible
                           options: easy, medium, hard
        """
        self.files_name = "exampleTest"
        self.SPLINE_DEGREE = 5              # Sharpness of curves
        self.MAX_TRIES = 500                # Maximum number of invalid generated points/segments
        self.POPULATION_SIZE = 5            # Minimum number of generated roads for each generation
        self.NUMBER_ELITES = 3              # Number of best kept roads
        self.MIN_SEGMENT_LENGTH = 28        # Minimum length of a road segment
        self.MAX_SEGMENT_LENGTH = 45        # Maximum length of a road segment
        self.WIDTH_OF_STREET = 5            # Width of all segments
        self.MIN_NODES = 8                  # Minimum number of control points for each road
        self.MAX_NODES = 12                 # Maximum number of control points for each road
        self.population_list = []
        self.set_difficulty(difficulty)

    def _bspline(self, control_points, samples=75):
        """ Calculate {@code samples} samples on a bspline
        :param control_points: Array of control points
        :param samples: Number of samples to return
        :return: Array with samples, representing a bspline of the given function
        """
        control_points = np.asarray(control_points)
        count = len(control_points)
        degree = np.clip(self.SPLINE_DEGREE, 1, count - 1)

        # Calculate knot vector.
        kv = np.concatenate(([0] * degree, np.arange(count - degree + 1), [count - degree] * degree))

        # Calculate query range.
        u = np.linspace(False, (count - degree), samples)

        # Calculate result.
        return np.array(si.splev(u, (kv, control_points.T, degree))).T

    def set_difficulty(self, difficulty):
        difficulty = difficulty.upper()
        if difficulty == "EASY":
            self.SPLINE_DEGREE = 7
            self.MIN_SEGMENT_LENGTH = 30
            self.MAX_SEGMENT_LENGTH = 50
            self.WIDTH_OF_STREET = 4
            self.MIN_NODES = 6
            self.MAX_NODES = 10
        elif difficulty == "MEDIUM":
            self.SPLINE_DEGREE = 5
            self.MIN_SEGMENT_LENGTH = 25
            self.MAX_SEGMENT_LENGTH = 45
            self.WIDTH_OF_STREET = 5
            self.MIN_NODES = 8
            self.MAX_NODES = 12
        elif difficulty == "HARD":
            self.SPLINE_DEGREE = 2
            self.MIN_SEGMENT_LENGTH = 20
            self.MAX_SEGMENT_LENGTH = 40
            self.WIDTH_OF_STREET = 6
            self.MIN_NODES = 12
            self.MAX_NODES = 16
        else:
            print(colored("Invalid difficulty level. Choosing default difficulty.", 'blue'))

    def _generate_random_points(self):
        """Generates random valid points and returns when the list is full or
         the number of invalid nodes equals the number of maximum tries.
         :return: Array of valid control points.
         """

        # Generating the first two points by myself.
        p0 = (1, 0)
        p1 = (65, 0)
        control_points = [p0, p1]
        iterator = 1
        tries = 0
        while len(control_points) != self.MAX_NODES and tries <= self.MAX_TRIES:
            new_point = self._generate_random_point(control_points[-1])
            temp_list = deepcopy(control_points)
            temp_list.append(new_point)
            spline_list = self._bspline(temp_list, 120)
            control_points_lines = convert_points_to_lines(spline_list)
            width_list = self._get_width_lines(spline_list)
            if not (intersection_check_last(control_points, new_point) or spline_intersection_check(spline_list)
                    or intersection_check_width(width_list, control_points_lines)):
                control_points.append(new_point)
                iterator = iterator + 1
                tries = 0
            else:
                tries += 1

        if len(control_points) < self.MIN_NODES:
            print(colored("Couldn't create enough valid nodes. Restarting...", "blue"))
        else:
            print(colored("Finished list!", "blue"))
            spline_list = self._bspline(control_points)
            if spline_intersection_check(spline_list):
                control_points.pop()
            if len(control_points) % 2 != 0:
                control_points.pop()
            return control_points

    def _generate_random_point(self, last_point):
        """Generates a random point within a given range.
        :param last_point: Last point of the control point list.
        :return: A new random point
        """
        last_point_tmp = (last_point[0], last_point[1])
        last_point_tmp = np.asarray(last_point_tmp)
        x_min = last_point[0] - self.MAX_SEGMENT_LENGTH
        x_max = last_point[0] + self.MAX_SEGMENT_LENGTH
        y_min = last_point[1] - self.MAX_SEGMENT_LENGTH
        y_max = last_point[1] + self.MAX_SEGMENT_LENGTH
        if x_min < 0:
            x_min = 0
        if y_min < 0:
            y_min = 0

        tries = 0
        x_min = int(round(x_min))
        x_max = int(round(x_max))
        y_min = int(round(y_min))
        y_max = int(round(y_max))
        while tries < self.MAX_TRIES / 10:
            x_pos = randint(x_min, x_max)
            y_pos = randint(y_min, y_max)
            point = (x_pos, y_pos)
            dist = np.linalg.norm(np.asarray(point) - last_point_tmp)
            if self.MAX_SEGMENT_LENGTH >= dist >= self.MIN_SEGMENT_LENGTH:
                return point
            tries += 1

    def _create_start_population(self):
        """Creates and returns start population."""
        startpop = []
        iterator = 0
        while len(startpop) < self.POPULATION_SIZE:
            point_list = self._generate_random_points()
            if point_list is not None:
                startpop.append([point_list, 0])
                build_xml(point_list, self.files_name + str(iterator), self.WIDTH_OF_STREET)
                iterator += 1
        return startpop

    def _mutation(self, individual):
        """Mutates a road by randomly picking one point and replacing it with
         a new, valid one.
         :param individual: Individual in the form of [control_points, fitness_value].
         :return: Mutated individual.
         """
        probability = 0.25
        print(colored("Mutating individual...", "blue"))
        iterator = 2
        while iterator < len(individual[0]):
            if random() <= probability:
                valid = False
                tries = 0
                while not valid and tries < self.MAX_TRIES / 10:
                    new_point = self._generate_random_point(individual[0][iterator - 1])
                    new_point = (new_point[0], new_point[1])
                    temp_list = deepcopy(individual[0])
                    temp_list[iterator] = new_point
                    spline_list = self._bspline(temp_list, 60)
                    control_points_lines = convert_points_to_lines(spline_list)
                    linestring_list = self._get_width_lines(spline_list)
                    if not (intersection_check_all(spline_list)
                            or intersection_check_width(linestring_list, control_points_lines)):
                        valid = True
                        individual[0][iterator] = new_point
                    tries += 1
            iterator += 1
        individual[1] = 0
        return individual

    def _crossover(self, parent1, parent2):
        """Performs a crossover between two parents.
        :param parent1: First parent
        :param parent2: Second parent
        :return: Valid children, which can be equal or different from the parents.
        """
        print(colored("Performing crossover of two individuals...", "blue"))
        probability = 0.25
        if len(parent1[0]) <= len(parent2[0]):
            smaller_index = len(parent1[0])
        else:
            smaller_index = len(parent2[0])
        iterator = 1
        tries = 0
        while tries < self.MAX_TRIES / 5:
            while iterator < smaller_index:
                child1 = deepcopy(parent1)
                child2 = deepcopy(parent2)
                if random() <= probability:
                    children = self._recombination(child1[0], child2[0], iterator)
                    child1 = children[0]
                    child2 = children[1]
                    width_list1 = self._get_width_lines(self._bspline(child1[0]))
                    width_list2 = self._get_width_lines(self._bspline(child2[0]))
                    control_lines1 = convert_points_to_lines(self._bspline(child1[0]))
                    control_lines2 = convert_points_to_lines(self._bspline(child2[0]))
                    if not (intersection_check_all(child1[0])
                            or intersection_check_all(child2[0])
                            or intersection_check_width(width_list1, control_lines1)
                            or intersection_check_width(width_list2, control_lines2)):
                        return [child1, child2]
                iterator += 1
            tries += 1
        return [parent1, parent2]

    @staticmethod
    def _recombination(parent1, parent2, separation_index):
        """Helper method of the crossover method. Recombinates two individuals
        on a given point. Can be seen as a single crossover.
        :param parent1: First parent
        :param parent2: Second parent
        :param separation_index: Point where the crossover should happen.
        :return: Return the two recombinated children. Can be invalid.
        """
        child1 = []
        child2 = []
        iterator = 0
        while iterator <= separation_index:
            child1.append(parent1[iterator])
            child2.append(parent2[iterator])
            iterator += 1
        while iterator < len(parent2):
            child1.append(parent2[iterator])
            iterator += 1
        iterator = separation_index + 1
        while iterator < len(parent1):
            child2.append(parent1[iterator])
            iterator += 1
        children = [[child1, 0], [child2, 0]]
        return children

    def _calculate_fitness_value(self, distances, ticks):
        """Calculates the fitness value of an individual by measuring the
        elapsed time and the cumulative distance to the center of the road.
        :param distances: List of traced distances.
        :param ticks: The AI frequency.
        :return: Void.
        """
        iterator = 0
        while iterator < self.POPULATION_SIZE:
            time = ticks / 60
            cumulative_distance = sum(distances)
            self.population_list[iterator][1] = cumulative_distance / time

            # Comment the three above lines and comment out the two following lines to use maximum distance as the
            # fitness function.
            # max_distance = max(distances)
            # self.population_list[iterator][1] = max_distance
            iterator += 1
            yield

    def _choose_elite(self, population):
        """Chooses the roads with the best fitness values.
        :param population: List of control points and its corresponding fitness values.
        :return: List of best x control points and its corresponding fitness values.
        """
        population.sort(key=itemgetter(1))
        elite = []
        iterator = 0
        while iterator < self.NUMBER_ELITES:
            elite.append(population[iterator])
            iterator += 1
        return elite

    def _get_resize_factor(self, length):
        """Returns the resize factor for the width lines so all lines have
        one specific length.
        :param length: Length of a LineString.
        :return: Resize factor
        """
        if length == 0:
            return 0
        return self.WIDTH_OF_STREET / length

    def _get_width_lines(self, control_points):
        """Determines the width lines of the road by flipping the LineString
         between two points by 90 degrees in both directions.
        :param control_points: List of control points
        :return: List of LineStrings which represent the width of the road.
        """
        spline_list = deepcopy(control_points)
        linestring_list = []
        iterator = 0
        while iterator < (len(spline_list) - 1):
            p1 = (spline_list[iterator][0], spline_list[iterator][1])
            p2 = (spline_list[iterator + 1][0], spline_list[iterator + 1][1])
            line = LineString([p1, p2])

            # Rotate counter-clockwise and resize to the half of the road length.
            line_rot1 = affinity.rotate(line, 90, line.coords[0])
            line_rot1 = affinity.scale(line_rot1, xfact=self._get_resize_factor(line_rot1.length),
                                       yfact=self._get_resize_factor(line_rot1.length),
                                       origin=line_rot1.coords[0])

            # Rotate clockwise and resize to the half of the road length.
            line_rot2 = affinity.rotate(line, -90, line.coords[0])
            line_rot2 = affinity.scale(line_rot2, xfact=self._get_resize_factor(line_rot2.length),
                                       yfact=self._get_resize_factor(line_rot2.length),
                                       origin=line_rot2.coords[0])

            line = LineString([line_rot1.coords[1], line_rot2.coords[1]])
            linestring_list.append(line)

            if iterator == len(spline_list) - 2:
                line = LineString([p1, p2])
                line_rot1 = affinity.rotate(line, -90, line.coords[1])
                line_rot1 = affinity.scale(line_rot1, xfact=self._get_resize_factor(line_rot1.length),
                                           yfact=self._get_resize_factor(line_rot1.length),
                                           origin=line_rot1.coords[0])

                line_rot2 = affinity.rotate(line, 90, line.coords[1])
                line_rot2 = affinity.scale(line_rot2, xfact=self._get_resize_factor(line_rot2.length),
                                           yfact=self._get_resize_factor(line_rot2.length),
                                           origin=line_rot2.coords[0])
                line = LineString([line_rot1.coords[1], line_rot2.coords[1]])
                line = affinity.scale(line, xfact=self._get_resize_factor(line.length)*2, yfact=self._get_resize_factor(line.length)*2)
                linestring_list.append(line)
            iterator += 1
        return linestring_list

    def _spline_population(self, population_list):
        """Converts the control points list of every individual to a bspline
         list and adds the width parameter.
        :param population_list: List of individuals
        :return: List of individuals with bsplined control points.
        """
        iterator = 0
        while iterator < len(population_list):
            population_list[iterator][0] = self._bspline(population_list[iterator][0])
            iterator += 1
        return population_list

    def genetic_algorithm(self):
        """The main algorithm to generate valid roads. Utilizes a genetic
         algorithm to evolve more critical roads for a AI.
        :return: Void. But it creates xml files.
        """
        if len(self.population_list) == 0:
            self.population_list = self._create_start_population()
        while len(self.population_list) < self.POPULATION_SIZE:
            selected_indices = sample(range(0, len(self.population_list)), 2)
            parent1 = self.population_list[selected_indices[0]]
            parent2 = self.population_list[selected_indices[1]]
            children = self._crossover(parent1, parent2)
            child1 = children[0]
            child2 = children[1]
            child1 = self._mutation(child1)
            child2 = self._mutation(child2)
            self.population_list.append(child1)
            self.population_list.append(child2)

        print(colored("Population finished.", "blue"))
        temp_list = deepcopy(self.population_list)
        temp_list = self._spline_population(temp_list)
        build_all_xml(temp_list, self.WIDTH_OF_STREET, self.files_name)

        # Comment out if you want to see the generated roads (blocks until you close all images)
        # plot_all(temp_list)
        self.population_list = self._choose_elite(self.population_list)

        # Introduce new individuals in the population.
        new_child1 = self._generate_random_points()
        self.population_list.append([new_child1, 0])
        # new_child2 = self._generate_random_points()
        # self.population_list.append([new_child2, 0])

    def set_files_name(self, new_name):
        """Sets a new name for the created xml files."""
        self.files_name = new_name

    def getTest(self) -> Optional[Tuple[Path, Path]]:
        """Returns the two first test files starting with "files_name".
        :return: Tuple of the path to the dbe and dbc file.
        """
        destination_path = path.dirname(path.realpath(__file__)) + "\\scenario"
        xml_names = destination_path + "\\" + self.files_name + "*"
        matches = glob(xml_names)
        iterator = 0
        self.genetic_algorithm()
        while iterator < self.POPULATION_SIZE * 2:
            yield Path(matches[iterator + 1]), Path(matches[iterator])
            iterator += 2

    def onTestFinished(self, sid, vid):
        """This method is called after a test was finished in DriveBuild.
        Also updates fitness value of an individual.
        :param sid: Simulation ID
        :param vid: Vehicle ID (only one participant)
        :return: Void.
        """
        # TODO Change service if your configuration differs.
        service = AIExchangeService("localhost", 8383)
        trace_data = service.get_trace(sid, vid)
        distances = []
        for i in range(0, len(trace_data)):
            distances.append(trace_data[i][3].data["egoLaneDist"].road_center_distance.distance)
        ticks = trace_data[-1][2]
        self._calculate_fitness_value(distances, ticks)


    # def move_files(self):
    #     """Moves specified xml files to the done folder.
    #     :param dbc: Full path to the dbc file.
    #     :param dbe: Full path to the dbe file.
    #     :return: Void.
    #     """
    #     for paths in self.getTest():
    #         dbe = paths[0]
    #         dbc = paths[1]
    #         destination_path = path.dirname(path.realpath(__file__)) + "\\done"
    #         filename_dbc = path.basename(path.normpath(dbc))
    #         filename_dbe = path.basename(path.normpath(dbe))
    #         move(dbc, path.join(destination_path, filename_dbc))
    #         move(dbe, path.join(destination_path, filename_dbe))