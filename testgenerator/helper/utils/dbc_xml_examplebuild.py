"""This example dbc builder class demonstrates how to use the methods of the dbc builder to create
a criteria xml file.
"""

from utils.dbc_xml_builder import DBCBuilder
import os

dbc = DBCBuilder()

dbc.define_name("Example Test")
dbc.environment_name("exampleXML")
dbc.steps_per_second(60)
dbc.ai_freq(6)

init_state = [6, 6, 0, "MANUAL", 50]
waypoint1 = [0, 4, 4, "_BEAMNG", 40]
waypoint2 = [61, 4, 5, "AUTONOMOUS"]
waypoints = [waypoint1, waypoint2]
participant_id = "ego"
model = "ETK800"
dbc.add_car(init_state, waypoints, participant_id, model)

vc_pos = [participant_id, -4, 4, 4]
sc_speed = [participant_id, 15]
dbc.add_precond_partic_sc_speed(vc_pos, sc_speed)

success_point = [participant_id, 61, 4, 5]
dbc.add_success_point(success_point)

dbc.add_failure_conditions(participant_id, "offroad")


scenario = os.getcwd() + "\\scenario"
if not os.path.exists(scenario):
    os.mkdir(scenario)

dbc.save_xml("exampleXML")
