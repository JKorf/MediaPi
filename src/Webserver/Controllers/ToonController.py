from flask import request

from Controllers.ToonManager import ToonManager
from Shared.Logger import Logger, LogVerbosity
from Shared.Util import to_JSON
from Webserver.APIController import app


class ToonController:

    @staticmethod
    @app.route('/toon', methods=['GET'])
    def get_toon_status():
        status = ToonManager().get_status()
        result = ThermostatInfo(
            status.active_state,
            status.current_displayed_temperature,
            status.current_set_point)

        return to_JSON(result)

    @staticmethod
    @app.route('/toon/details', methods=['GET'])
    def get_toon_details():
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

    @staticmethod
    @app.route('/toon/gas', methods=['GET'])
    def get_gas_details():
        start_hours = request.args.get('startHours')
        end_hours = int(request.args.get('endHours'))
        if end_hours == 0:
            end_hours = 0.001
        stats = ToonManager().get_gas_stats(start_hours + " hours ago", str(end_hours) + " hours ago", "hours")
        return to_JSON(stats)

    @staticmethod
    @app.route('/toon/electricity', methods=['GET'])
    def get_electricity_details():
        start_hours = request.args.get('startHours')
        end_hours = request.args.get('endHours')

        stats = ToonManager().get_electricity_stats(start_hours + " hours ago", end_hours + " hours ago")
        return to_JSON(stats)

    @staticmethod
    @app.route('/toon/temperature', methods=['POST'])
    def set_temperature():
        temp = int(request.args.get('temp'))

        temp /= 100
        Logger().write(LogVerbosity.Info, "Setting toon temperature to " + str(temp))
        ToonManager().set_temperature(temp)
        return "OK"

    @staticmethod
    @app.route('/toon/state', methods=['POST'])
    def set_active_state():
        state = request.args.get('state')

        Logger().write(LogVerbosity.Info, "Setting toon state to " + state)
        ToonManager().set_state(state)
        return "OK"


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
    def __init__(self, name, state_id, temp, dhw):
        self.name = name
        self.id = state_id
        self.temp = temp
        self.dhw = dhw


class ThermostatInfo:

    def __init__(self, active_state, current_display_temp, current_setpoint):
        self.active_state = active_state
        self.current_display_temp = current_display_temp
        self.current_setpoint = current_setpoint
