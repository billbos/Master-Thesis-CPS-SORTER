"""This class builds an environment XML file for DriveBuild in the required format."""

import xml.etree.ElementTree as ElementTree
from os import path
import os
from os import remove
from pathlib import Path
from shutil import move


class DBEBuilder:

    def __init__(self):
        # Build a tree structure.
        self.root = ElementTree.Element("environment")
        self.root.set("xmlns", "http://drivebuild.com")
        self.root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        self.root.set("xsi:schemaLocation", "http://drivebuild.com drivebuild.xsd")
        self.author = ElementTree.SubElement(self.root, "author")
        self.author.text = "Michael Heine"

        # Change the light value of the environment as you like.
        self.timeOfDay = ElementTree.SubElement(self.root, "timeOfDay")
        self.timeOfDay.text = "0"

        self.lanes = ElementTree.SubElement(self.root, "lanes")

    def indent(self, elem, level=0):
        """Pretty prints a xml file.
        :param elem: XML tag.
        :param level: Number of empty spaces, initially zero (meaning it starts only a new line).
        :return: Void.
        """
        i = "\n" + level * "    "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "    "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def add_obstacles(self, obstacle_list):
        """Adds obstacles to the XML files.
        :param obstacle_list: Array of obstacles. First value is the shape/name of the obstacles,
                              the other parameters are defining the obstacle.
        :return: Void.
        """
        obstacles = ElementTree.SubElement(self.root, "obstacles")
        for obstacle in obstacle_list:
            if obstacle[0] == "cube":
                ElementTree.SubElement(obstacles, 'cube x="{}" y="{}" width="{}" length="{}"'
                                                  ' height="{}"'
                                       .format(obstacle[1], obstacle[2], obstacle[3], obstacle[4],
                                               obstacle[5]))
            elif obstacle[0] == "cylinder":
                ElementTree.SubElement(obstacles, 'cylinder x="{}" y="{}" radius="{}" height="{}"'
                                       .format(obstacle[1], obstacle[2], obstacle[3], obstacle[4]))
            elif obstacle[0] == "cone":
                ElementTree.SubElement(obstacles, 'cone x="{}" y="{}" height="{}" baseRadius="{}"'
                                       .format(obstacle[1], obstacle[2], obstacle[3], obstacle[4]))
            elif obstacle[0] == "bump":
                ElementTree.SubElement(obstacles, 'bump x="{}" y="{}" width="{}" length="{}" height="{}"'
                                                  ' upperLength="{}" upperWidth="{}"'
                                       .format(obstacle[1], obstacle[2], obstacle[3], obstacle[4],
                                               obstacle[5], obstacle[6], obstacle[7]))

    def add_lane(self, segments, markings=True, left_lanes=0, right_lanes=0):
        """Adds a lane and road segments.
        :param segments: Array of tuples containing nodes to generate road segments. Segments must have
                         x-coordinate, y-coordinate and width.
        :param markings: {@code True} Enables road markings, {@code False} makes them invisible.
        :param left_lanes: number of left lanes (int)
        :param right_lanes: number of right lanes (int)
        :return: Void
        """
        lane = ElementTree.SubElement(self.lanes, "lane")
        if markings:
            lane.set("markings", "true")
        if left_lanes != 0:
            lane.set("leftLanes", left_lanes)
        if right_lanes != 0:
            lane.set("rightLanes", right_lanes)
        for segment in segments:
            ElementTree.SubElement(lane, 'laneSegment x="{}" y="{}" width="{}"'
                                   .format(segment[0], segment[1], segment[2]))

    def save_xml(self, name):
        """Creates and saves the XML file, and moves it to the scenario folder.
        :param name: Desired name of this file.
        :return: Void, but it creates a XML file.
        """
        # Wrap it in an ElementTree instance, and save as XML.
        tree = ElementTree.ElementTree(self.root)
        self.indent(self.root)
        full_name = name + '.dbe.xml'

        current_path_of_file = Path(os.getcwd())
        current_path_of_file = os.path.realpath(current_path_of_file) + "\\" + full_name

        destination_path = Path(os.getcwd())
        destination_path = os.path.realpath(destination_path) + "\\scenario"

        tree.write(full_name, encoding="utf-8", xml_declaration=True)

        # Delete old files with the same name.
        if path.exists(destination_path + "\\" + full_name):
            remove(destination_path + "\\" + full_name)

        # Move created file to scenario folder.
        print('Path {}'.format(destination_path))
        move(current_path_of_file, destination_path)
