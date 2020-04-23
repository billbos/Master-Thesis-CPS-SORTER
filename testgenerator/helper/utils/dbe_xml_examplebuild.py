"""This example dbe builder class demonstrates how to use the methods of the dbe builder to create
an environment xml file.
"""

from utils.dbe_xml_builder import DBEBuilder
import os

dbe = DBEBuilder()

segment1 = [0, 0, 8]
segment2 = [50, 0, 8]
segment3 = [80, 20, 8]
segment4 = [100, 20, 8]
segments = [segment1, segment2, segment3, segment4]

dbe.add_lane(segments)

cone = ["cone", 5, 5, 5, 5]
cylinder = ["cylinder", 10, 10, 2, 2]
obstacles = [cone, cylinder]

dbe.add_obstacles(obstacles)

scenario = os.getcwd() + "\\scenario"
if not os.path.exists(scenario):
    os.mkdir(scenario)

dbe.save_xml("exampleXML")
