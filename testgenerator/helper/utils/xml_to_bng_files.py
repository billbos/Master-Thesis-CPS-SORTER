"""This class converts xml files to beamng json and prefab files."""

from drivebuildclient.AIExchangeService import AIExchangeService
from pathlib import Path
from glob import glob
from subprocess import call
from termcolor import colored
import os


def get_next_test(files_name):
    """Returns the next test files.
    :param files_name: File name series.
    :return: dbc and dbe file paths in a list.
    """
    destination_path = Path(os.getcwd())
    destination_path = os.path.realpath(destination_path) + "\\scenario"
    xml_names = destination_path + "\\" + files_name + "*"
    matches = glob(xml_names)
    if len(matches) > 1:
        return [matches[0], matches[1]]


def convert_test(files_name):
    """Starts a test in DriveBuild to convert xml files to prefab and json files.
    :return: Void.
    """
    next_test = get_next_test(files_name)
    dbc = next_test[0]
    dbe = next_test[1]
    service = AIExchangeService("localhost", 8383)
    service.run_tests("test", "test", Path(dbe), Path(dbc))
    print(colored("Starting DriveBuild to generate BeamNG files...", "blue"))
    # Close BeamNG after converting
    call("taskkill /f /im BeamNG.research.x64.exe", shell=True)
