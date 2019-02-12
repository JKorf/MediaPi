from Controllers.ToonManager import ToonManager
from Shared.Logger import Logger
from Shared.Util import to_JSON
from Webserver.BaseHandler import BaseHandler


class ToonController(BaseHandler):
    def get(self, url):
        if url == "get_status":
            self.write(self.get_toon_status())
        elif url == "get_details":
            self.write(self.get_toon_details())

    def post(self, url):
        if url == "set_temperature":
            self.set_temperature(int(self.get_argument("temperature")))
        elif url == "set_active_state":
            self.set_active_state(self.get_argument("state"))

    def get_toon_status(self):
        status = ToonManager().get_status()
        result = ThermostatInfo(
            status.active_state,
            status.current_displayed_temperature,
            status.current_set_point)

        return to_JSON(result)

    def get_toon_details(self):
        status = ToonManager().get_status()
        states = ToonManager().get_states()

        result = ThermostatDetails(
            status.active_state,
            status.current_displayed_temperature,
            status.current_modulation_level,
            status.current_set_point,
            status.next_program,
            status.next_set_point,
            status.next_state,
            status.next_time,
            status.program_state,
            status.real_set_point,
            [ThermostatState(x.name, x.id, x.temperature, x.dhw) for x in states if x.id != 4])

        return to_JSON(result)

    def set_temperature(self, temp):
        temp /= 100
        Logger.write(2, "Setting toon temperature to " + str(temp))
        ToonManager().set_temperature(temp)

    def set_active_state(self, state):
        Logger.write(2, "Setting toon state to " + state)
        ToonManager().set_state(state)


class ThermostatDetails:
    def __init__(self, active_state, current_display_temp, current_modulation_lvl, current_setpoint, next_program, next_setpoint, next_state, next_time, program_state, real_setpoint, states):
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
        self.states = states


class ThermostatState:
    def __init__(self, name, id, temp, dhw):
        self.name = name
        self.id = id
        self.temp = temp
        self.dhw = dhw


class ThermostatInfo:

    def __init__(self, active_state, current_display_temp, current_setpoint):
        self.active_state = active_state
        self.current_display_temp = current_display_temp
        self.current_setpoint = current_setpoint