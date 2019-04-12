import React, { Component } from 'react';
import { Link } from "react-router-dom";

import axios from 'axios';

import Button from './../../Components/Button';
import CheckBox from './../../Components/CheckBox';
import TimePicker from './../../Components/TimePicker';
import ViewLoader from './../../Components/ViewLoader';
import LightGroupSelector from './../../Components/LightGroupSelector';
import SelectConditionPopup from './../../Components/Popups/SelectConditionPopup';

class RuleView extends Component {
  constructor(props) {
    super(props);
    this.state = { showSelectConditionType:false, currentRules: [], rule: { id: -1, conditions: [], action: {}}};

    this.props.functions.changeBack({ to: "/home/rules" });
    this.props.functions.changeTitle("Rule");
    this.props.functions.changeRightImage(null);

    this.newRule = this.props.match.params.id == -1

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
            if(this.newRule)
                this.changeAction(1);
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

    if (this.state.rule.conditions.length == 0){
        alert("Rule needs at least one condition");
        e.preventDefault();
        return;
    }

    var paramLength = this.state.rule.action.parameters.length;
    var paramString = "";
    for (var i = 0; i < paramLength; i++)
        paramString += "&param" + (i + 1) + "=" +this.state.rule.action.parameters[i];

    var conditionLength = this.state.rule.conditions.length;
    var conditionString = "&conditions=" + conditionLength;
    for (var i = 0; i < conditionLength; i++)
    {
        conditionString += "&condition"+i+"_type=" + this.state.rule.conditions[i].type;
        for (var j = 0; j < this.state.rule.conditions[i].parameters.length; j++)
            conditionString += "&condition"+i+"_param" + (j + 1) + "=" +this.state.rule.conditions[i].parameters[j]
    }

    axios.post(window.vars.apiBase + 'rule/save?id=' + this.state.rule.id +
                            "&name=" + this.state.rule.name +
                            "&active=" + this.state.rule.active +
                            "&action_id=" + this.state.rule.action.id +
                            paramString + conditionString);

    if (this.newRule){
        return;
    }

    window.setTimeout(this.getRule, 500);
  }

  getConditionById(id){
    return this.state.conditions.filter(c => c.id == id)[0]
  }

  getActionById(id){
    return this.state.actions.filter(c => c.id == id)[0]
  }

  paramChange(item, parameter_index, newValue)
  {
    console.log(newValue);
    item.parameters[parameter_index] = newValue;
    this.setState({rule: this.state.rule});
  }

  paramHourChange(item, parameter_index, newValue)
  {
    item.parameters[parameter_index] = (item.parameters[parameter_index] % 60) + newValue * 60;
    console.log(item.parameters[parameter_index]);
    this.setState({rule: this.state.rule});
  }

  paramMinuteChange(item, parameter_index, newValue)
  {
    item.parameters[parameter_index] = (item.parameters[parameter_index] - item.parameters[parameter_index] % 60) + parseInt(newValue);
    console.log(item.parameters[parameter_index]);
    this.setState({rule: this.state.rule});
  }

  removeCondition(condition)
  {
    this.state.rule.conditions.splice(this.state.rule.conditions.indexOf(condition), 1);
    this.setState({rule: this.state.rule});
  }

  changeAction(targetId)
  {
    var action = this.getActionById(targetId);
    var newParams = this.createParametersForItem(action);
    this.state.rule.action.id = targetId;
    this.state.rule.action.parameters = newParams;
    this.setState({rule: this.state.rule});
  }

  createParametersForItem(item)
  {
      var result = [];
      for (var i = 0; i < item.parameter_description.length; i++)
      {
        var type = item.parameter_description[i][1];
        if (type == "bool")
            result.push(false);
        else if(type == "int" || type == "time")
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
                            { condition.parameter_description[index][1] == "bool" &&
                                <div><CheckBox value={param} onChange={(newVal) => this.paramChange(cond, index, newVal)} /> </div>
                            }
                            { condition.parameter_description[index][1] == "int" &&
                                <div><input type="number" value={ param } onChange={(e) => this.paramChange(cond, index, e.target.value)}/> </div>
                            }
                            { condition.parameter_description[index][1] == "time" &&
                                <div><TimePicker hour={Math.floor(param / 60)} minute={param % 60} onHourChange={(newVal) => this.paramHourChange(cond, index, newVal)} onMinuteChange={(newVal) => this.paramMinuteChange(cond, index, newVal)} /></div>
                            }
                            { condition.parameter_description[index][1] == "light_group" &&
                                <div>Select light</div>
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
    var action = this.getActionById(act.id);
    var item =
             this.state.rule.action.parameters.map((param, index) =>
                <div className="rule-condition-parameter" key={index}>
                    <div className="rule-condition-parameter-name">{ action.parameter_description[index][0] }:</div>
                    <div className="rule-condition-parameter-value">
                        { action.parameter_description[index][1] == "bool" &&
                            <div><CheckBox value={param} onChange={(newVal) => this.paramChange(act, index, newVal)} /> </div>
                        }
                        { action.parameter_description[index][1] == "int" &&
                            <div><input className="rule-number-parameter" type="number" value={ param } onChange={(e) => this.paramChange(act, index, e.target.value)}/> </div>
                        }
                        { action.parameter_description[index][1] == "time" &&
                            <div><TimePicker hour={Math.floor(param / 60)} minute={param % 60} onHourChange={(newVal) => this.paramHourChange(act, index, newVal)} onMinuteChange={(newVal) => this.paramMinuteChange(action, index, newVal)} /></div>
                        }
                        { action.parameter_description[index][1] == "light_group" &&
                            <div><LightGroupSelector value={param} onChange={(newVal) => this.paramChange(act, index, newVal)} /></div>
                        }
                    </div>
                </div>
            )

    return item
  }

  addNewCondition(type){
    var condition = this.getConditionById(type);
    console.log(condition);
    console.log(this.state.rule);
    var newParams = this.createParametersForItem(condition);
    this.state.rule.conditions.push({id: -1, type: type, parameters: newParams });
    this.setState({rule: this.state.rule, showSelectConditionType: false});
  }

  setName(name)
  {
    this.state.rule.name = name;
    this.setState({rule: this.state.rule});
  }

  setActive(value)
  {
    this.state.rule.active = value;
    this.setState({rule: this.state.rule});
  }

  render() {
    if (!this.state.actions)
        return "";

    var conditionItems = [];
    for(var i = 0; i < this.state.rule.conditions.length; i++){
        conditionItems.push(this.getConditionItem(this.state.rule.conditions[i]));
    }

    return (
      <div className="rule-view">
        <div className="rule-name">
            <div className="rule-name-label">Name:</div>
            <div className="rule-name-input"><input value={this.state.rule.name} onChange={(e) => { this.setName(e.target.value) }} type="text" placeholder="rule name" /></div>
        </div>
        <div className="rule-name">
            <div className="rule-name-label">Active:</div>
            <div className="rule-name-input"><CheckBox value={this.state.rule.active} onChange={(newValue) => { this.setActive(newValue) }} /></div>
        </div>

        <div className="rule-summary">
            <div className="rule-title">Summary</div>
            <div className="rule-description">{ this.state.rule.description }</div>
        </div>

        <div className="rule-conditions">
            <div className="rule-title">Conditions</div>
            {conditionItems}
            <div className="rule-condition-add" onClick={() => { this.setState({showSelectConditionType: true}) }}>
                + add condition
            </div>
            { this.state.showSelectConditionType &&
                <SelectConditionPopup conditionTypes={this.state.conditions} onCancel={() => { this.setState({showSelectConditionType: false}) }} onSelect={(selected) => {this.addNewCondition(selected)}} />
            }
        </div>

        <div className="rule-action">
            <div className="rule-title">Action</div>
            { this.state.actions && this.state.rule.action.parameters &&
                <div className="rule-action-inner">
                    <div className="rule-action-select">
                        <span className="rule-condition-name">Action to execute:</span>
                        <select className="rule-action-select-field" value={this.state.rule.action.id} onChange={(e) => { this.changeAction(parseInt(e.target.value)) }}>
                            { this.state.actions.map(action =>
                                <option key={action.id} value={action.id}>{action.name}</option>
                            )}
                        </select>
                    </div>
                    <div className="rule-action-parameters">
                        {this.getActionItem(this.state.rule.action)}
                    </div>
                </div>
            }
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