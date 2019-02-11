from Controllers.ToonManager import ToonManager
from Shared.Util import to_JSON
from Webserver.BaseHandler import BaseHandler


class ToonController(BaseHandler):
    def get(self, url):
        if url == "get_status":
            self.write(self.get_toon_status())

    def post(self, url):
        if url == "set_temperature":
            self.set_temperature(float(self.get_argument("temperature")))

    def get_toon_status(self):
        status = ToonManager().get_status()
        result = ThermostatInfo(
            status.active_state,
            status.current_displayed_temperature,
            status.current_modulation_level,
            status.current_set_point,
            status.next_program,
            status.next_set_point,
            status.next_state,
            status.next_time,
            status.program_state,
            status.real_set_point)

        return to_JSON(result)

    def set_temperature(self, temp):
        ToonManager().set_temperature(temp)

class ThermostatInfo:

    def __init__(self, active_state, current_display_temp, current_modulation_lvl, current_setpoint, next_program, next_setpoint, next_state, next_time, program_state, real_setpoint):
        self.active_state = active_state
        self.current_display_temp = current_display_temp
        self.current_modulation_lvl = current_modulation_lvl
        self.current_setpoint = current_setpoint
        self.next_program = next_program
        self.next_setpoint = next_setpoint
        self.next_state = next_state
        self.next_time = next_time
        self.program_state = program_state
        self.real_setpoint = real_setpoint