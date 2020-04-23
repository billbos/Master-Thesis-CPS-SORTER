import subprocess
import signal
from time import sleep
import os

from drivebuildclient.AIExchangeService import AIExchangeService
from drivebuildclient.aiExchangeMessages_pb2 import SimStateResponse, VehicleID

from lxml.etree import parse
from lxml.etree import tostring
import importlib.util
import sys

from test_generator import TestGenerator


my_env = os.environ
my_env["PATH"] = "C:\\sbse4tac-ws-2019-self-driving-car-e2edriving\\venv\\Scripts\\python.exe"
env_path = "C:\\sbse4tac-ws-2019-self-driving-car-e2edriving\\venv\\Scripts\\python.exe"


def kill_process(process):
    if process:
        if os.name == 'nt':
            subprocess.call(
                ['taskkill', '/F', '/T', '/PID', str(process.pid)])
        else:
            os.kill(process.pid, signal.SIGTERM)
        return True
    return False


def main():
    print("parameters: ")
    for i in range(1, len(sys.argv)):
        print(sys.argv[i])
    data_request_path = sys.argv[1]
    ai_path = sys.argv[2]
    working_directory = sys.argv[3]
    """
    data_request_path = "C:\\sbse4tac-ws-2019-self-driving-car-e2edriving\\ai\\data_requests.py"
    ai_path = "C:\\sbse4tac-ws-2019-self-driving-car-e2edriving\\run_db.py"
    working_directory = "C:\\sbse4tac-ws-2019-self-driving-car-e2edriving"
    """

    service = AIExchangeService("localhost", 8383)

    vid = VehicleID()
    vid.vid = "ego"

    tg = TestGenerator()
    tg.set_difficulty("easy")
    while True:
        for paths in tg.getTest():
            criteria = paths[1]
            environment = paths[0]

            # edit the xml
            spec = importlib.util.spec_from_file_location("AI",
                                                          data_request_path)
            foo = importlib.util.module_from_spec(spec)
            # Actually run the import
            spec.loader.exec_module(foo)

            # get ai element
            double_backslash_dbc_path = str(criteria).replace("\\", "\\" + "\\")
            tree = parse(double_backslash_dbc_path)
            root = tree.getroot()
            for i in range(0, len(root.getchildren())):
                if root.getchildren()[i].tag == "{http://drivebuild.com}participants":
                    participant_block = root.getchildren()[i].getchildren()[0]
                    for j in range(0, len(participant_block)):
                        part_child = participant_block.getchildren()[j]
                        if part_child.tag == "{http://drivebuild.com}ai":
                            pass
                            part_child.clear()
                            foo.add_data_requests(part_child, "ego")
                            pass
            # write the changed xml
            # TODO pretty print
            f = open(double_backslash_dbc_path, "w")
            f.write(tostring(root, pretty_print=True).decode("utf-8"))
            f.close()

            # ai: _Element = ai_tag.makeelement(_tag="speed")

            submission_result = service.run_tests("test", "test", environment, criteria)
            # Interact with a simulation
            if submission_result and submission_result.submissions:
                for test_name, sid in submission_result.submissions.items():
                    # with ...


                    # Michael, Tim, Felix
                    ai_process = subprocess.Popen([env_path, ai_path, sid.sid], cwd=working_directory)

                    # Manoj, Yuki, Dinesh
                    # ai_process = subprocess.Popen(["C:\\sbse4tac-ws-2019-self-driving-car-smartcars\\.venv\\Scripts\\python.exe",
                    #                               "C:\\sbse4tac-ws-2019-self-driving-car-smartcars\\integration_with_DriveBuild\\trained_ai.py",
                    #                               sid.sid],
                    #                            cwd="C:\\sbse4tac-ws-2019-self-driving-car-smartcars\\integration_with_DriveBuild")

                    sim_state = service.wait_for_simulator_request(sid, vid)
                    while sim_state is SimStateResponse.SimState.RUNNING:
                        sleep(5)
                        sim_state = service.wait_for_simulator_request(sid, vid)

                    # TODO Use a trap or try except to ensure we kill the process
                    kill_process(ai_process)
                    sleep(5)
                    tg.onTestFinished(sid, vid)


if __name__ == '__main__':
    main()
    pass
