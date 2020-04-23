"""This file offers several plotting methods to visualize functions or roads."""

import matplotlib.pyplot as plt
import numpy as np


def plotter(control_points):
    """Plots every point and lines between them. Used to visualize a road.
    :param control_points: List of points as tuples [(x, y),...]
    :return: Void.
    """
    control_points = np.asarray(control_points)
    x = control_points[:, 0]
    y = control_points[:, 1]

    plt.plot(x, y, '-og', markersize=1, linewidth=2)
    plt.xlim([min(x) - 0.3, max(x) + 0.3])
    plt.ylim([min(y) - 0.3, max(y) + 0.3])

    plt.title('Road overview')
    plt.show()


def plot_all(population):
    """Plots a whole population. Method starts a new figure for every individual.
    :param population: Population in form of [[control_points, fitness_value],...]
    :return: Void
    """
    iterator = 0
    while iterator < len(population):
        plotter(population[iterator][0])
        iterator += 1


def plot_lines(lines):
    """Plots LineStrings of the package shapely. Can be also used to plot other geometries.
    :param lines: List of lines, e.g. LineStrings
    :return: Void
    """
    iterator = 0
    while iterator < len(lines):
        x, y = lines[iterator].xy
        plt.plot(x, y, '-og', markersize=3)
        iterator += 1
    # plt.show()


def plot_splines_and_width(width_lines, control_point_lines):
    """Plots connected control points with their width lines.
    :param width_lines: List of lines (e.g. LineStrings) which represent the width of a road segment.
    :param control_point_lines: List of connected control points (e.g. LineStrings).
    :return: Void.
    """
    plot_lines(width_lines)
    plot_lines(control_point_lines)
    plt.show()
