import React, { Component } from 'react';
import { Link } from "react-router-dom";

import axios from 'axios';

import Button from './../../Components/Button';
import CheckBox from './../../Components/CheckBox';
import TimePicker from './../../Components/TimePicker';
import TradfriGroupSelector from './../../Components/TradfriGroupSelector';
import InstanceSelector from './../../Components/InstanceSelector';
import RadioSelector from './../../Components/RadioSelector';
import SelectConditionPopup from './../../Components/Popups/SelectConditionPopup';

class RuleView extends Component {
  constructor(props) {
    super(props);
    this.state = { showSelectConditionType:false, actions: [], rule: { id: -1, active: true, conditions: [], actions: []}};

    this.props.functions.changeBack({ to: "/home/rules" });
    this.props.functions.changeTitle("Rule");
    this.props.functions.changeRightImage(null);

    this.newRule = this.props.match.params.id === "-1";

    this.saveRule = this.saveRule.bind(this);
    this.getConditionById = this.getConditionById.bind(this);
    this.getActionById = this.getActionById.bind(this);
    this.getConditionItem = this.getConditionItem.bind(this);
    this.getActionItem = this.getActionItem.bind(this);
    this.getRule = this.getRule.bind(this);
  }

  componentDidMount() {
   axios.get(window.vars.apiBase + 'rules/actions_and_conditions').then(
        (data) => {
            data = data.data;
            console.log(data);
            this.setState({actions: data[0], conditions: data[1]});
         },
        (error) => { console.log(error) }
    )

    if (this.newRule){
        return;
    }

    this.getRule();
  }

  getRule()
  {
    axios.get(window.vars.apiBase + 'rule?id=' + this.props.match.params.id).then(
        (data) => {
            data = data.data;
            console.log(data);
            this.setState({rule: data});
         },
        (error) => { console.log(error) }
    )
  }

  saveRule(e)
  {
    if (!this.state.rule.name){
        alert("Name can't be empty");
        e.preventDefault();
        return;
    }

    if (this.state.rule.conditions.length === 0){
        alert("Rule needs at least one condition");
        e.preventDefault();
        return;
    }

    var actionsLength = this.state.rule.actions.length;
    var actionString = "&actions=" + actionsLength;
    for (var i = 0; i < actionsLength; i++)
    {
        actionString += "&action"+i+"_type=" + this.state.rule.actions[i].type;
        for (var j = 0; j < this.state.rule.actions[i].parameters.length; j++)
            actionString += "&action"+i+"_param" + (j + 1) + "=" +this.state.rule.actions[i].parameters[j];
    }

    var conditionLength = this.state.rule.conditions.length;
    var conditionString = "&conditions=" + conditionLength;
    for (var k = 0; k < conditionLength; k++)
    {
        conditionString += "&condition"+k+"_type=" + this.state.rule.conditions[k].type;
        for (var l = 0; l < this.state.rule.conditions[k].parameters.length; l++)
            conditionString += "&condition"+k+"_param" + (l + 1) + "=" +this.state.rule.conditions[k].parameters[l];
    }

    axios.post(window.vars.apiBase + 'rule/save?id=' + this.state.rule.id +
                            "&name=" + this.state.rule.name +
                            "&active=" + this.state.rule.active +
                            actionString + conditionString);

    if (this.newRule){
        return;
    }

    window.setTimeout(this.getRule, 500);
  }

  getConditionById(id){
    return this.state.conditions.filter(c => c.id === id)[0]
  }

  getActionById(id){
    return this.state.actions.filter(c => c.id === id)[0]
  }

  paramChange(item, parameter_index, newValue)
  {
    item.parameters[parameter_index] = newValue;
    this.setState({rule: this.state.rule});
  }

  paramHourChange(item, parameter_index, newValue)
  {
    item.parameters[parameter_index] = (item.parameters[parameter_index] % 60) + newValue * 60;
    this.setState({rule: this.state.rule});
  }

  paramMinuteChange(item, parameter_index, newValue)
  {
    item.parameters[parameter_index] = (item.parameters[parameter_index] - item.parameters[parameter_index] % 60) + parseInt(newValue);
    this.setState({rule: this.state.rule});
  }

  removeCondition(condition)
  {
    this.state.rule.conditions.splice(this.state.rule.conditions.indexOf(condition), 1);
    this.setState({rule: this.state.rule});
  }

  removeAction(action)
  {
    this.state.rule.actions.splice(this.state.rule.actions.indexOf(action), 1);
    this.setState({rule: this.state.rule});
  }

  createParametersForItem(item)
  {
      var result = [];
      for (var i = 0; i < item.parameter_description.length; i++)
      {
        var type = item.parameter_description[i][1];
        if (type === "bool")
            result.push(false);
        else if(type === "int" || type === "time")
            result.push(0);
        else
            result.push("");
      }
      return result;
  }

  getConditionItem(cond){
    var condition = this.getConditionById(cond.type);
    var item =
        <div className="rule-condition" key={condition.id}>
            <div className="rule-condition-name">`{condition.name}` condition</div>
            <div className="rule-condition-parameters">
                { cond.parameters.map((param, index) =>
                    <div className="rule-condition-parameter" key={index}>
                        <div className="rule-condition-parameter-name">{ condition.parameter_description[index][0] }:</div>
                        <div className="rule-condition-parameter-value">
                            { condition.parameter_description[index][1] === "bool" &&
                                <div><CheckBox value={param} onChange={(newVal) => this.paramChange(cond, index, newVal)} /> </div>
                            }
                            { condition.parameter_description[index][1] === "int" &&
                                <div><input type="number" value={ param } onChange={(e) => this.paramChange(cond, index, e.target.value)}/> </div>
                            }
                            { condition.parameter_description[index][1] === "time" &&
                                <div><TimePicker hour={Math.floor(param / 60)} minute={param % 60} onHourChange={(newVal) => this.paramHourChange(cond, index, newVal)} onMinuteChange={(newVal) => this.paramMinuteChange(cond, index, newVal)} /></div>
                            }
                            { condition.parameter_description[index][1] === "tradfri_group" &&
                                <div><TradfriGroupSelector value={param} onChange={(newVal) => this.paramChange(cond, index, newVal)} /></div>
                            }
                            { condition.parameter_description[index][1] === "instance" &&
                                <div><InstanceSelector value={param} onChange={(newVal) => this.paramChange(cond, index, newVal)} /></div>
                            }
                            { condition.parameter_description[index][1] === "radio" &&
                                <div><RadioSelector value={param} onChange={(newVal) => this.paramChange(cond, index, newVal)} /></div>
                            }
                        </div>
                    </div>
                ) }
            </div>
            <div className="rule-condition-remove" onClick={() => this.removeCondition(cond)}>
                X
            </div>
        </div>

    return item
  }

  getActionItem(act){
    var action = this.getActionById(act.type);
    var item =
        <div className="rule-condition" key={action.id}>
            <div className="rule-condition-name">`{action.name}` action</div>
            <div className="rule-condition-parameters">
             { act.parameters.map((param, index) =>
                <div className="rule-condition-parameter" key={index}>
                    <div className="rule-condition-parameter-name">{ action.parameter_description[index][0] }:</div>
                    <div className="rule-condition-parameter-value">
                        { action.parameter_description[index][1] === "bool" &&
                            <div><CheckBox value={param} onChange={(newVal) => this.paramChange(act, index, newVal)} /> </div>
                        }
                        { action.parameter_description[index][1] === "int" &&
                            <div><input className="rule-number-parameter" type="number" value={ param } onChange={(e) => this.paramChange(act, index, e.target.value)}/> </div>
                        }
                        { action.parameter_description[index][1] === "time" &&
                            <div><TimePicker hour={Math.floor(param / 60)} minute={param % 60} onHourChange={(newVal) => this.paramHourChange(act, index, newVal)} onMinuteChange={(newVal) => this.paramMinuteChange(action, index, newVal)} /></div>
                        }
                        { action.parameter_description[index][1] === "tradfri_group" &&
                            <div><TradfriGroupSelector value={param} onChange={(newVal) => this.paramChange(act, index, newVal)} /></div>
                        }
                        { action.parameter_description[index][1] === "instance" &&
                            <div><InstanceSelector value={param} onChange={(newVal) => this.paramChange(act, index, newVal)} /></div>
                        }
                        { action.parameter_description[index][1] === "radio" &&
                            <div><RadioSelector value={param} onChange={(newVal) => this.paramChange(act, index, newVal)} /></div>
                        }
                    </div>
                </div>
            ) }
            </div>
            <div className="rule-condition-remove" onClick={() => this.removeAction(action)}>
                X
            </div>
        </div>

    return item
  }

  addNewCondition(type){
    var condition = this.getConditionById(type);
    var newParams = this.createParametersForItem(condition);
    this.state.rule.conditions.push({id: -1, type: type, parameters: newParams });
    this.setState({rule: this.state.rule, showSelectConditionType: false});
  }

  addNewAction(type){
    var action = this.getActionById(type);
    var newParams = this.createParametersForItem(action);
    this.state.rule.actions.push({id: -1, type: type, parameters: newParams });
    this.setState({rule: this.state.rule, showSelectActionType: false});
  }

  setName(name)
  {
    var rule = this.state.rule;
    rule.name = name;
    this.setState({rule: rule});
  }

  setActive(value)
  {
  var rule = this.state.rule;
    rule.active = value;
    this.setState({rule: rule});
    this.setState({rule: this.state.rule});
  }

  render() {
    if (this.state.actions.length === 0)
        return "";

    var actionItems = [];
    for(var i = 0; i < this.state.rule.actions.length; i++){
        actionItems.push(this.getActionItem(this.state.rule.actions[i]));
    }

    var conditionItems = [];
    for(var j = 0; j < this.state.rule.conditions.length; j++){
        conditionItems.push(this.getConditionItem(this.state.rule.conditions[j]));
    }

    return (
      <div className="rule-view">
        <div className="rule-general">
            <div className="rule-title">General</div>
            <div className="rule-item-inner rule-general-inner">
                <div className="rule-general-item">
                    <div className="rule-name-label">Name:</div>
                    <div className="rule-name-input"><input value={this.state.rule.name} onChange={(e) => { this.setName(e.target.value) }} type="text" placeholder="rule name" /></div>
                </div>
                <div className="rule-general-item">
                    <div className="rule-name-label">Active:</div>
                    <div className="rule-name-input"><CheckBox value={this.state.rule.active} onChange={(newValue) => { this.setActive(newValue) }} /></div>
                </div>
            </div>
        </div>

        { !this.newRule &&
            <div className="rule-summary">
                <div className="rule-title">Summary</div>
                <div className="rule-description">{ this.state.rule.description }</div>
            </div>
        }

        <div className="rule-conditions">
            <div className="rule-title">Conditions</div>
            <div className="rule-item-inner">
                {conditionItems}
                { this.state.rule.conditions.length === 0 &&
                    <div className="rule-condition rule-no-item">No conditions yet</div>
                }
                <div className="rule-condition-add" onClick={() => { this.setState({showSelectConditionType: true}) }}>
                    + add condition
                </div>
                { this.state.showSelectConditionType &&
                    <SelectConditionPopup actionType="action" conditionTypes={this.state.conditions} onCancel={() => { this.setState({showSelectConditionType: false}) }} onSelect={(selected) => {this.addNewCondition(selected)}} />
                }
            </div>
        </div>

        <div className="rule-actions">
            <div className="rule-title">Actions</div>
            <div className="rule-item-inner">
                {actionItems}
                { this.state.rule.actions.length === 0 &&
                    <div className="rule-condition rule-no-item">No actions yet</div>
                }
                <div className="rule-condition-add" onClick={() => { this.setState({showSelectActionType: true}) }}>
                    + add action
                </div>
                { this.state.showSelectActionType &&
                    <SelectConditionPopup actionType="action" conditionTypes={this.state.actions} onCancel={() => { this.setState({showSelectActionType: false}) }} onSelect={(selected) => {this.addNewAction(selected)}} />
                }
            </div>
        </div>

        <div className="rule-save-button">
            { !this.newRule &&
                <Button text="Save" classId="secondary" onClick={() => this.saveRule()}/>
            }
            { this.newRule &&
                <Link to="/home/rules"><Button text="Save" classId="secondary" onClick={(e) => this.saveRule(e)}/></Link>
            }
        </div>
      </div>
    );
  }
};

export default RuleView;