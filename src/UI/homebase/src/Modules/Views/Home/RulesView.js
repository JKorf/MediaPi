import React, { Component } from 'react';
import axios from 'axios';
import { Link } from "react-router-dom";
import { formatTime } from './../../../Utils/Util.js';

import Button from './../../Components/Button';
import CheckBox from './../../Components/CheckBox';

class RulesView extends Component {
  constructor(props) {
    super(props);
    this.state = { currentRules: []};

    this.props.functions.changeBack({ to: "/home/" });
    this.props.functions.changeTitle("Rules");
    this.props.functions.changeRightImage(null);

    this.removeRule = this.removeRule.bind(this);
  }

  componentDidMount() {
    axios.get(window.vars.apiBase + 'rules').then(
        (data) => {
            data = data.data;
            console.log(data);
            this.setState({rulesEnabled: data[0], currentRules: data[1]});
         },
        (error) => { console.log(error) }
    )
  }

  removeRule(rule)
  {
      if(window.confirm("Do want to remove rule: " + rule.name + " ?"))
      {
         this.state.currentRules.splice(this.state.currentRules.indexOf(rule), 1)
         this.setState({currentRules: this.state.currentRules});
         axios.post(window.vars.apiBase + 'rule/remove?id=' + rule.id);
      }
  }

  toggleEnabled(value)
  {
    axios.post(window.vars.apiBase + "rules/enable?val=" + value);
    this.setState({rulesEnabled: value});
  }

  render() {

    return (
      <div className="rules-view">
          <div className="current-rules">
              <div className="rules-header">
                <div className="rules-header-column rules-header-name">name</div>
                <div className="rules-header-column rules-header-last-run">Last run</div>
                <div className="rules-header-column rules-header-active">Active</div>
                <div className="rules-header-column"></div>
              </div>
              { this.state.currentRules.length === 0 &&
                <div className="no-rules">No rules yet</div>
              }
              { this.state.currentRules.map(rule =>
                  <div key={rule.id} className={"current-rule " + (rule.active ? "": "inactive") + (this.state.selectedRule === rule ? "selected": "")}>
                    <div className="current-rule-row">
                        <div className="current-rule-name" onClick={() => this.setState({selectedRule: rule})}>{rule.name}</div>
                        <div className="current-rule-last-execution">{(rule.last_execution === 0 ? "never": formatTime(rule.last_execution, false, true, true, true, true))}</div>
                        <div className="current-rule-active">
                            <CheckBox value={rule.active} readonly />
                        </div>
                        <div className="current-rule-controls">
                            <Link to={"/home/rule/" + rule.id}><div className="current-rule-edit">edit</div></Link>
                            <div className="current-rule-remove" onClick={() => this.removeRule(rule)}>remove</div>
                        </div>
                    </div>
                    { this.state.selectedRule === rule &&
                        <div className="current-rule-selected">
                            {rule.description}
                        </div>
                    }
                  </div>
              ) }
          </div>

          <div className="rule-add-btn"><Link to={"/home/rule/-1"}><Button text="Add rule" classId="secondary"/></Link></div>


        <div className="rule-enabled-checkbox">
            <div className="rule-enabled-checkbox-label">Rules enabled:</div>
            <div className="rule-enabled-checkbox-input"><CheckBox value={this.state.rulesEnabled} onChange={(newValue) => this.toggleEnabled(newValue)} /></div>
        </div>
      </div>
    );
  }
};

export default RulesView;