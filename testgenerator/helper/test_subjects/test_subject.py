import threading
from abc import ABC, abstractmethod


class TestSubject(ABC, threading.Thread):

    @abstractmethod
    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        while self.running:
            self.step()

    def stop(self):
        self.running = False

    @abstractmethod
    def step(self):
        pass