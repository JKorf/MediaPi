import React, { Component } from 'react';
import axios from 'axios';

import { formatTemperature, formatTime } from './../../../Utils/Util.js';
import { InfoGroup } from './../../Components/InfoGroup';
import ViewLoader from './../../Components/ViewLoader';
import { ResponsiveContainer, LineChart, XAxis, YAxis, Tooltip, Line } from 'recharts';

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

    var end = (new Date).getTime();
    var start = end - 1000 * 60 * 60 * 24 * 7;
    axios.get(window.vars.apiBase + 'util/get_action_history?topic=temperature&start=' + start + "&end=" + end).then(
        (data) => {
            for (var i = 0; i < data.data.length; i++)
                data.data[i].param1 = parseInt(data.data[i].param1);
            this.setState({historyData: data.data});
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

        if (this.timer)
            clearTimeout(this.timer);
        this.timer = setTimeout(() => {
            axios.post(window.vars.apiBase + 'toon/temperature?temperature=' + this.state.thermostatData.current_setpoint).then(
                (data) => {
                    console.log(data);
                 },
                (error) => { console.log(error) }
            )
        }, 750);
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

  render() {
    var currentState = {};
    var nextState = {};
    var nextTime = "";

    if(this.state.thermostatData){
        var date = new Date(0);
        date.setUTCSeconds(this.state.thermostatData.next_time);
        nextTime = formatTime(date, false, false, false, true, true);
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
                <div className="info-group-box heating-box">
                     <div className="heating-current-temp">
                        <div className="heating-current-header">current</div>
                        <div className="heating-current-value">{formatTemperature(this.state.thermostatData.current_display_temp)}</div>
                    </div>
                    <div className="heating-set-temp">

                        <div className="heating-current-setpoint">
                            <div className="heating-current-setpoint-header">target</div>
                            <div className="heating-current-setpoint-value">{formatTemperature(this.state.thermostatData.current_setpoint)}</div>
                        </div>
                        <div className="heating-current-controls">
                            <div className="heating-increase-temp" onClick={() => this.changeTemp(50)}>+</div>
                            <div className="heating-decrease-temp" onClick={() => this.changeTemp(-50)}>-</div>
                        </div>
                    </div>
                </div>
            </InfoGroup>

            <InfoGroup title="State">
                <div className="info-group-box heating-box">
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
                                    <div className="heating-state-current-temp">{formatTemperature(currentState.temp)}</div>
                                </div>
                            }
                        </div>

                        { nextState &&
                            <div className="heating-state-next">
                                <div className="heating-state-next-header">next at {nextTime}</div>
                                <div className="heating-state-next-name">{nextState.name}</div>
                                <div className="heating-state-next-temp">{formatTemperature(nextState.temp)}</div>
                            </div>
                        }
                    </div>
                </div>
            </InfoGroup>

            <InfoGroup title="History">
                { this.state.historyData &&
                    <ResponsiveContainer width="100%" height={200}>
                        <LineChart data={this.state.historyData} margin={{top:20,right:30,bottom:30,left:-10}}>
                          <XAxis angle={20}
                                 dy={20}
                                 interval="preserveStartEnd"
                                 dataKey="timestamp"
                                 tickFormatter = {(timestamp) => formatTime(timestamp, false, true, true, true, true)}
                                 />
                          <YAxis dataKey="param1" type="number" domain={['dataMin - 2', 'dataMax + 2']}/>
                          <Line dataKey="param1" stroke="#8884d8" dot={false} animationDuration={500} />
                          <Tooltip content={<CustomTooltip />} />
                        </LineChart>
                    </ResponsiveContainer>
                }
            </InfoGroup>
            </div>
        }
      </div>
    );
  }
};

const CustomTooltip = ({ active, payload, label }) => {
	if (active) {
		return (
			<div className="custom-tooltip">
				<div className="label">{formatTime(label, false, true, true, true, true)}</div>
				<div>{payload[0].value}°C</div>
				<div className="desc">
				{ payload[0].payload.caller == "user" && <span>Set by user</span> }
				{ payload[0].payload.caller == "rule" && <span>Set by rule</span> }
				</div>
			</div>
		);
	}

	return null;
};

export default HeatingView;