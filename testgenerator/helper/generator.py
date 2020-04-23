# from logging import getLogger
# from os.path import join, dirname
# from pathlib import Path

# from jinja2 import Environment, FileSystemLoader
# from typing import Dict, List, Tuple, Optional

# from asfault.tests import RoadTest
# from lxml.etree import _Element

# ENV_SIZE: float = 100
# TEMPLATE_PATH = join(dirname(__file__), "..", "templates")
# TEMPLATE_ENV = Environment(loader=FileSystemLoader(TEMPLATE_PATH))
# DBE_TEMPLATE_NAME = "reference_environment.dbe.xml"
# DBC_TEMPLATE_NAME = "reference_criteria.dbc.xml"
# _logger = getLogger("SubmissionTester.ReferenceGenerator")

# LaneNode = Dict[str, float]
# Lane = List[LaneNode]


# class ReferenceTestGenerator:
#     @staticmethod
#     def _configure_asfault() -> None:
#         from asfault.config import init_configuration, load_configuration
#         from tempfile import TemporaryDirectory
#         temp_dir = TemporaryDirectory(prefix="testGenerator")
#         init_configuration(temp_dir.name)
#         load_configuration(temp_dir.name)

#     @staticmethod
#     def _generate_test_id() -> str:
#         return "test_id"  # FIXME Implement generation of test IDs

#     @staticmethod
#     def _generate_asfault_test() -> RoadTest:
#         from asfault.generator import RoadGenerator
#         from asfault.tests import get_start_goal_coords
#         from shapely.geometry import box
#         from numpy.random.mtrand import randint
#         test_id = ReferenceTestGenerator._generate_test_id()
#         while True:
#             generator = RoadGenerator(box(-ENV_SIZE, -ENV_SIZE, ENV_SIZE, ENV_SIZE), randint(10000))
#             test_stub = RoadTest(test_id, generator.network, None, None)
#             while generator.grow() != generator.done:
#                 pass
#             if test_stub.network.complete_is_consistent():
#                 candidates = generator.network.get_start_goal_candidates()
#                 # FIXME Choose candidate based on some ranking?
#                 if candidates:
#                     start, goal = candidates.pop()
#                     paths = generator.network.all_paths(start, goal)
#                     # FIXME Choose candidate based on some ranking?
#                     for path in paths:
#                         start_coords, goal_coords = get_start_goal_coords(generator.network, start, goal)
#                         test = RoadTest(test_id, generator.network, start_coords, goal_coords)
#                         test.set_path(path)
#                         return test

#     @staticmethod
#     def _get_lanes(test: RoadTest) -> List[Lane]:
#         from asfault.beamer import prepare_streets
#         streets = prepare_streets(test.network)
#         for street in streets:
#             lane_nodes = street["nodes"]
#             for node in lane_nodes:
#                 node["width"] = float("{0:.2f}".format(round(node["width"], 2)))
#         return list(map(lambda street: street["nodes"], streets))

#     @staticmethod
#     def _generate_dbe(lanes: List[Lane]) -> str:
#         return TEMPLATE_ENV.get_template(DBE_TEMPLATE_NAME) \
#             .render(lanes=lanes)

#     @staticmethod
#     def _generate_dbc(lane_to_follow: Lane, dbe_file_name: str, steps_per_second: int = 10, ai_frequency: int = 5,
#                       test_name: str = "Test") -> Tuple[str, str]:
#         from numpy import rad2deg, arctan2, array, pi, cos, sin
#         goal = lane_to_follow[-1]
#         current = lane_to_follow[0]
#         current_pos = array([current["x"], current["y"]])
#         next = lane_to_follow[1]
#         next_pos = array([next["x"], next["y"]])
#         delta = next_pos - current_pos
#         initial_orientation_rad = arctan2(delta[1], delta[0])
#         initial_orientation_deg = float("{0:.2f}".format(rad2deg(initial_orientation_rad)))
#         # NOTE Do NOT merge the following lines until the next note. It screws up the calculation.
#         r2 = 0.25 * current["width"]
#         theta2 = initial_orientation_rad - 0.5 * pi
#         offset = array([2.5 * cos(initial_orientation_rad), 2.5 * sin(initial_orientation_rad)])
#         temp = current_pos + offset
#         initial_position = temp + array([r2 * cos(theta2), r2 * sin(theta2)])
#         initial_state = {"x": initial_position[0], "y": initial_position[1]}
#         # NOTE Do NOT merge the previous lines until the previous note.
#         # FIXME Is only able to handle a single participant
#         dbc_content = TEMPLATE_ENV.get_template(DBC_TEMPLATE_NAME) \
#             .render(testName=test_name,
#                     initial_state=initial_state,
#                     lane=lane_to_follow,
#                     dbe_file_name=dbe_file_name,
#                     goal=goal,
#                     movementMode="AUTONOMOUS",
#                     stepsPerSecond=steps_per_second,
#                     aiFrequency=ai_frequency,
#                     orientation=initial_orientation_deg)
#         dbc_reference_content = TEMPLATE_ENV.get_template(DBC_TEMPLATE_NAME) \
#             .render(testName=test_name + "_reference",
#                     initial_state=initial_state,
#                     lane=lane_to_follow,
#                     waypoints=[lane_to_follow[-1]],
#                     dbe_file_name=dbe_file_name,
#                     goal=goal,
#                     movementMode="_BEAMNG",
#                     stepsPerSecond=steps_per_second,
#                     aiFrequency=ai_frequency,
#                     orientation=initial_orientation_deg)
#         return dbc_content, dbc_reference_content

#     @staticmethod
#     def get_points_of_goal_area(node: _Element) -> List[Tuple[float, float]]:
#         serialized_points = node.get("points")
#         points = []
#         for point_tuple in serialized_points.split(";"):
#             coos = point_tuple[1:-1].split(",")
#             points.append((float(coos[0]), float(coos[1])))
#         return points

#     @staticmethod
#     def create_reference_test(dbe_file_path: Path, dbc_file_path: Path) -> Optional[Path]:
#         from xml_util import parse_xml, findall, find
#         from lxml.etree import tostring
#         from tempfile import NamedTemporaryFile
#         from test_types import determine_target_positions, set_target_position, extend_goal_region
#         dbe_tree = parse_xml(dbe_file_path)
#         dbc_tree = parse_xml(dbc_file_path)
#         # Change test name
#         test_name_node = find(dbc_tree, "//db:name")
#         test_name_node.text = test_name_node.text + "_reference"
#         # Modify movement modes
#         movement_mode_nodes = findall(dbc_tree, "//*[@movementMode]")
#         for node in movement_mode_nodes:
#             node.set("movementMode", "_BEAMNG")

#         target_positions = determine_target_positions(dbe_tree, dbc_tree)
#         participant_nodes = findall(dbc_tree, "//db:participant")
#         for participant_node in participant_nodes:
#             participant_id = participant_node.get("id")
#             # FIXME Change all participants? What about MANUAL mode?
#             # Modify movement description
#             target_position, invalid_goal_area = target_positions[participant_id]
#             if target_position:
#                 set_target_position(participant_node, target_position)
#                 if invalid_goal_area:
#                     extend_goal_region(dbc_tree, participant_id, target_position)
#             else:
#                 _logger.debug("Could not find a candidate for a final destination waypoint.")
#                 return None
#         with NamedTemporaryFile(mode="wb", delete=False, suffix=".dbc.xml") as temp_dbc_file:
#             temp_dbc_file.write(tostring(dbc_tree))
#         return Path(temp_dbc_file.name)

#     @staticmethod
#     def generate_random_test(test_name: str = "Test") -> List[Path]:
#         from tempfile import NamedTemporaryFile
#         from os.path import basename
#         ReferenceTestGenerator._configure_asfault()
#         test = ReferenceTestGenerator._generate_asfault_test()
#         lanes = ReferenceTestGenerator._get_lanes(test)

#         dbe_content = ReferenceTestGenerator._generate_dbe(lanes)
#         with NamedTemporaryFile(mode="w", delete=False, suffix=".dbe.xml") as temp_dbe_file:
#             temp_dbe_file.write(dbe_content)

#         # FIXME Choose lane based on some ranking?
#         dbc_content, dbc_reference_content \
#             = ReferenceTestGenerator._generate_dbc(lanes[0], basename(temp_dbe_file.name), test_name=test_name)
#         with NamedTemporaryFile(mode="w", delete=False, suffix=".dbc.xml") as temp_dbc_file:
#             temp_dbc_file.write(dbc_content)
#         with NamedTemporaryFile(mode="w", delete=False, suffix=".dbc.xml") as temp_dbc_reference_file:
#             temp_dbc_reference_file.write(dbc_reference_content)

#         return [Path(temp_file.name) for temp_file in [temp_dbe_file, temp_dbc_file, temp_dbc_reference_file]]


# class RandomGenerator:
#     @staticmethod
#     def getTest() -> Optional[Tuple[Path, Path]]:
#         # FIXME Assumes that the first entry is a DBE and the third entry is the reference DBC
#         test_files = ReferenceTestGenerator.generate_random_test()
#         return test_files[0], test_files[1]
# #