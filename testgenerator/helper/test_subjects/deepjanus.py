import numpy as np
from beamngpy.sensors import Camera

from ai import deepjanus
from test_subjects.test_subject import TestSubject


class DeepJanus(TestSubject):

    def __init__(self, ego_vehicle, bng, model_path=None):
        super().__init__()
        self.vehicle = ego_vehicle
        self.bng = bng
        self.ai = deepjanus.AI(model_path)
        pos = (-0.3, 2.1, 0.3)
        direction = (0, np.pi, 0)
        fov = 120
        resolution = (320, 160)
        cam_center = Camera(pos, direction, fov, resolution, colour=True,
                            depth=True, annotation=True)
        self.vehicle.attach_sensor('cam_center', cam_center)

    def step(self):
        sensors = self.bng.poll_sensors(self.vehicle)
        image = sensors['cam_center']['colour'].convert('RGB')
        vel = self.vehicle.state['vel']
        speed = np.sqrt(vel[0] * vel[0] + vel[1] * vel[1]) * 3.6
        steering_angle, throttle = self.ai.predict(image, speed)
        self.vehicle.control(throttle=throttle, steering=steering_angle)
