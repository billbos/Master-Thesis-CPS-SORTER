from shapely.geometry import LineString


def convert_points_to_lines(control_points):
    """Turns a list of points into a list of LineStrings.
    :param control_points: List of points
    :return: List of LineStrings
    """
    control_points_lines = []
    iterator = 0
    while iterator < (len(control_points) - 1):
        p1 = (control_points[iterator][0], control_points[iterator][1])
        p2 = (control_points[iterator + 1][0], control_points[iterator + 1][1])
        line = LineString([p1, p2])
        control_points_lines.append(line)
        iterator += 1
    return control_points_lines
