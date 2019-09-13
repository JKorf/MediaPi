import React, { Component } from 'react';
import axios from 'axios';

import { formatTemperature, formatTime } from './../../../Utils/Util.js';
import { InfoGroup } from './../../Components/InfoGroup';
import ViewLoader from './../../Components/ViewLoader';
import { ResponsiveContainer, LineChart, XAxis, YAxis, Tooltip, Line } from 'recharts';
import Socket from './../../../Socket2.js';

class HeatingView extends Component {
  constructor(props) {
    super(props);
    this.state = {};

    this.props.functions.changeBack({ to: "/home/" });
    this.props.functions.changeTitle("Heating");
    this.props.functions.changeRightImage(null);

    this.changeTemp = this.changeTemp.bind(this);
    this.devicesUpdate = this.devicesUpdate.bind(this);
  }

  componentDidMount() {
    this.devicesSub = Socket.subscribe("device:ToonThermostat", this.devicesUpdate);

    var end = new Date().getTime();
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

  componentWillUnmount(){
     Socket.unsubscribe(this.devicesSub);
  }

  devicesUpdate(subId, data){
    console.log(data);
    this.setState(data);
    this.setState({loading: false});
  }

  changeTemp(delta){
       var newTemp = this.state.setpoint + delta;
       this.setState({setpoint: newTemp});

        if (this.timer)
            clearTimeout(this.timer);
        this.timer = setTimeout(() => {
            axios.post(window.vars.apiBase + 'home/set_setpoint?device_id=ToonThermostat&temperature=' + this.state.setpoint).then(
                (data) => {
                    console.log(data);
                 },
                (error) => { console.log(error) }
            )
        }, 750);
  }

  render() {
    var currentState = {};
    var nextState = {};
    var nextTime = "";

    return (
      <div className="heating-view">
        <ViewLoader loading={!this.state.setpoint}/>
        { this.state.setpoint &&
            <div className="heating-view-content">
            <InfoGroup title="Temperature">
                <div className="info-group-box heating-box">
                     <div className="heating-current-temp">
                        <div className="heating-current-header">current</div>
                        <div className="heating-current-value">{formatTemperature(this.state.temperature)}</div>
                    </div>
                    <div className="heating-set-temp">

                        <div className="heating-current-setpoint">
                            <div className="heating-current-setpoint-header">target</div>
                            <div className="heating-current-setpoint-value">{formatTemperature(this.state.setpoint)}</div>
                        </div>
                        <div className="heating-current-controls">
                            <div className="heating-increase-temp" onClick={() => this.changeTemp(1)}>+</div>
                            <div className="heating-decrease-temp" onClick={() => this.changeTemp(-1)}>-</div>
                        </div>
                    </div>
                </div>
            </InfoGroup>

            { this.state.historyData && this.state.historyData.length > 1 &&

                <InfoGroup title="History">
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
                </InfoGroup>
            }

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
				{ payload[0].payload.caller === "user" && <span>Set by user</span> }
				{ payload[0].payload.caller === "rule" && <span>Set by rule</span> }
				</div>
			</div>
		);
	}

	return null;
};

export default HeatingView;