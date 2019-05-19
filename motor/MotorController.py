import RPi.GPIO as GPIO
import time


class MotorController:

    steps_forward = [
        [1, 0, 0, 0],
        [1, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 1, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 1],
        [1, 0, 0, 1]
    ]
    steps_back = reversed(steps_forward)

    def __init__(self, pins, ms_sleep, steps_per_revolution):
        self.pins = pins
        self.sleep = 0.001 * ms_sleep
        self.steps_per_revolution = steps_per_revolution

    def init(self):
        GPIO.setmode(GPIO.BOARD)
        for pin in self.pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)

    def cleanup(self):
        GPIO.cleanup()

    def move_steps(self, steps):
        if steps > 0:
            step_data = MotorController.steps_forward
        else:
            step_data = MotorController.steps_back

        for i in range(steps):
            for half_step in range(8):
                self.__do_step(half_step, step_data)
                time.sleep(self.sleep)

    def move_angle(self, angle):
        steps = self.steps_per_revolution / (360 / abs(angle))
        if angle < 0:
            steps = -steps
        self.move_steps(int(round(steps)))

    def __do_step(self, half_step, step_data):
        for pin in range(4):
            GPIO.output(self.pins[pin], step_data[half_step][pin])
