import React, { Component } from 'react';
import axios from 'axios';

import { InfoGroup } from './../../Components/InfoGroup';
import ViewLoader from './../../Components/ViewLoader';

class HeatingView extends Component {
  constructor(props) {
    super(props);
    this.state = {};

    this.props.functions.changeBack({ to: "/home/" });
    this.props.functions.changeTitle("Heating");
    this.props.functions.changeRightImage(null);

    this.setActiveState = this.setActiveState.bind(this);
    this.changeTemp = this.changeTemp.bind(this);
  }

  componentDidMount() {
    axios.get(window.vars.apiBase + 'toon/details').then(
        (data) => {
            this.setState({thermostatData: data.data});
            console.log(data.data);
         },
        (error) => { console.log(error) }
    )
  }

  changeTemp(delta){
    var newTemp = this.state.thermostatData.current_setpoint + delta;
    var old = this.state.thermostatData;
    old.current_setpoint = newTemp;
    old.active_state = -1;
    this.setState({thermostatData: old});

    axios.post(window.vars.apiBase + 'toon/temperature?temperature=' + newTemp).then(
        (data) => {
            console.log(data);
         },
        (error) => { console.log(error) }
    )
  }

  setActiveState(state){
    var old = this.state.thermostatData;
    old.active_state = state.id;
    old.current_setpoint = state.temp;
    this.setState({thermostatData: old});
    axios.post(window.vars.apiBase + 'toon/state?state=' + state.name).then(
        (data) => {
            console.log(data);
         },
        (error) => { console.log(error) }
    )
  }

  formatTemperature(value){
     return (Math.round(value / 10) / 10) + "°C";
  }

  render() {
    var currentState = {};
    var nextState = {};
    var nextTime = "";

    if(this.state.thermostatData){
        var date = new Date(0);
        date.setUTCSeconds(this.state.thermostatData.next_time);
        nextTime = new Intl.DateTimeFormat('en-GB', { hour: 'numeric', minute: 'numeric' }).format(date);
        currentState = this.state.thermostatData.states.filter(x => x.id === this.state.thermostatData.active_state)[0];
        if(!currentState)
            currentState = {id: -1, temp: this.state.thermostatData.real_setpoint, name: "Manual"};
        nextState = this.state.thermostatData.states.filter(x => x.id === this.state.thermostatData.next_state)[0];
    }
    return (
      <div className="heating-view">
        <ViewLoader loading={!this.state.thermostatData}/>
        { this.state.thermostatData &&
            <div className="heating-view-content">
            <InfoGroup title="Temperature">
                <div className="player-group-details">
                     <div className="heating-current-temp">
                        <div className="heating-current-header">current</div>
                        <div className="heating-current-value">{this.formatTemperature(this.state.thermostatData.current_display_temp)}</div>
                    </div>
                    <div className="heating-set-temp">

                        <div className="heating-current-setpoint">
                            <div className="heating-current-setpoint-header">target</div>
                            <div className="heating-current-setpoint-value">{this.formatTemperature(this.state.thermostatData.current_setpoint)}</div>
                        </div>
                        <div className="heating-current-controls">
                            <div className="heating-increase-temp" onClick={() => this.changeTemp(50)}>+</div>
                            <div className="heating-decrease-temp" onClick={() => this.changeTemp(-50)}>-</div>
                        </div>
                    </div>
                </div>
            </InfoGroup>

            <InfoGroup title="State">
                <div className="player-group-details">
                    <div className="heating-states">
                        { this.state.thermostatData.states.map(state =>
                            <div key={state.id} className={"heating-state " + (state.id === this.state.thermostatData.active_state ? "selected": "")} onClick={() => this.setActiveState(state)}>{state.name}</div>
                        ) }
                    </div>

                    <div className="heating-state-details">
                        <div className="heating-state-current">
                            { currentState &&
                                <div>
                                    <div className="heating-state-current-header">current</div>
                                    <div className="heating-state-current-name">{currentState.name}</div>
                                    <div className="heating-state-current-temp">{this.formatTemperature(currentState.temp)}</div>
                                </div>
                            }
                        </div>

                        <div className="heating-state-next">
                            <div className="heating-state-next-header">next at {nextTime}</div>
                            <div className="heating-state-next-name">{nextState.name}</div>
                            <div className="heating-state-next-temp">{this.formatTemperature(nextState.temp)}</div>
                        </div>
                    </div>
                </div>
            </InfoGroup>
            </div>
        }
      </div>
    );
  }
};

export default HeatingView;