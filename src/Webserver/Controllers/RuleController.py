from flask import request

from Controllers.RuleManager import RuleManager
from Database.Database import Database
from Shared.Logger import Logger, LogVerbosity
from Shared.Util import to_JSON
from Webserver.APIController import app


class RuleController:
    @staticmethod
    @app.route('/rules/actions_and_conditions', methods=['GET'])
    def get_actions_and_conditions():
        Logger().write(LogVerbosity.Debug, "Getting rules")
        return to_JSON(RuleManager().get_actions_and_conditions())

    @staticmethod
    @app.route('/rules', methods=['GET'])
    def get_rules():
        Logger().write(LogVerbosity.Debug, "Getting rules")
        return to_JSON(RuleManager().get_rules())

    @staticmethod
    @app.route('/rule', methods=['GET'])
    def get_rule():
        rule_id = int(request.args.get('id'))
        Logger().write(LogVerbosity.Debug, "Getting rule " +str(rule_id))

        return to_JSON(RuleManager().get_rule(rule_id))

    @staticmethod
    @app.route('/rule/save', methods=['POST'])
    def save_rule():
        rule_id = int(request.args.get('id'))
        name = request.args.get('name')
        active = request.args.get('active') == "true"
        action_id = int(request.args.get('action_id'))
        param1 = request.args.get('param1')
        param2 = request.args.get('param2')
        param3 = request.args.get('param3')
        param4 = request.args.get('param4')
        param5 = request.args.get('param5')

        conditions = []
        conditions_length = int(request.args.get('conditions'))
        for i in range(conditions_length):
            condition_type = int(request.args.get('condition' + str(i) + "_type"))
            condition_param1 = request.args.get('condition' + str(i) + "_param1")
            condition_param2 = request.args.get('condition' + str(i) + "_param2")
            condition_param3 = request.args.get('condition' + str(i) + "_param3")
            condition_param4 = request.args.get('condition' + str(i) + "_param4")
            condition_param5 = request.args.get('condition' + str(i) + "_param5")
            conditions.append((condition_type, condition_param1, condition_param2, condition_param3, condition_param4, condition_param5))

        RuleManager().update_rule(rule_id, active, action_id, name, param1, param2, param3, param4, param5, conditions)
        return "OK"

    @staticmethod
    @app.route('/rule/remove', methods=['POST'])
    def remove_rule():
        rule_id = int(request.args.get('id'))
        RuleManager().remove_rule(rule_id)
        return "OK"
