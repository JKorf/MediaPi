import React, { Component } from 'react';
import axios from 'axios';
import { ResponsiveContainer, LineChart, XAxis, YAxis, Tooltip, Line } from 'recharts';
import { formatTemperature, formatTime } from './../../../Utils/Util.js';


import { InfoGroup } from './../../Components/InfoGroup';
import Switch from './../../Components/Switch';
import Slider from './../../Components/Slider';
import ViewLoader from './../../Components/ViewLoader';

import Socket from './../../../Socket2.js';

class AutomationDeviceView extends Component {
  constructor(props) {
    super(props);

    this.newGroup = this.props.match.params.id === "-1";

    this.props.functions.changeBack({ to: "/home/automation" });
    this.props.functions.changeTitle("Device");
    this.props.functions.changeRightImage(null);

    this.state = {id: this.props.match.params.id, loaded: false, historyDataType: "temperature", loading: true};
    this.devicesUpdate = this.devicesUpdate.bind(this);
  }

  componentDidMount() {
      this.devicesSub = Socket.subscribe("device:" + this.props.match.params.id, this.devicesUpdate);
  }

  componentWillUnmount(){
       Socket.unsubscribe(this.devicesSub);
  }

  devicesUpdate(subId, data){
    console.log(data);
    if(!this.state.loaded)
    {
        var topic = "temperature";
        if(data.device_type === "Switch")
            topic = "active";
        if(data.device_type === "Light")
            topic = "on";
        this.setState({historyDataType: topic});


        var end = new Date().getTime();
        var start = end - 1000 * 60 * 60 * 24 * 7;
        axios.get(window.vars.apiBase + 'util/get_action_history?device_id='+this.props.match.params.id+'&topic='+topic+'&start=' + start + "&end=" + end).then(
            (data) => {
                console.log(data);
                if (topic === "temperature"){
                    for (var i = 0; i < data.data.length; i++)
                        data.data[i].value = parseInt(data.data[i].value);
                }
                else{
                    for (var j = 0; j < data.data.length; i++)
                        data.data[j].value = data.data[j].value === "1" ? "on": "off";
                }
                this.setState({historyData: data.data});
             },
            (error) => { console.log(error) }
        )

    }

    this.setState(data);
    this.setState({loaded: true, loading: false});
  }

  saveName()
  {
      axios.post(window.vars.apiBase + 'home/set_device_name?device_id=' + this.state.id + "&name=" + encodeURIComponent(this.state.name));
  }

  toggleLight(value)
  {
      this.setState({state: value});
      axios.post(window.vars.apiBase + 'home/set_light_state?device_id=' + this.state.id + "&state=" + value);
  }

  lightDimmerChange(value)
  {
      this.setState({dim: value});
      axios.post(window.vars.apiBase + 'home/set_light_dimmer?device_id=' + this.state.id + "&dim=" + value);
  }

  lightWarmthChange(value)
  {
      this.setState({warmth: value});
      axios.post(window.vars.apiBase + 'home/set_light_warmth?device_id=' + this.state.id + "&warmth=" + value);
  }

   changeTemperature(value){
       this.setState({setpoint: this.state.setpoint + value});

        if (this.timer)
            clearTimeout(this.timer);
        this.timer = setTimeout(() => {
            axios.post(window.vars.apiBase + 'home/set_setpoint?device_id=' +this.state.id+ '&temperature=' + this.state.setpoint).then(
                (data) => {
                    console.log(data);
                 },
                (error) => { console.log(error) }
            )
        }, 750);
  }

  writePercentage(value)
  {
    return Math.round(value) + "%";
  }

  retryConnection(){
    this.setState({loading: true});
    axios.post(window.vars.apiBase + 'home/retry_connection?id='+ this.state.id).then(
        (data) => {
            this.setState({loading: false});
         },
        (error) => { this.setState({loading: false}); }
    );
  }

  render() {
    return (
        <div className="automation-view">
            <ViewLoader loading={this.state.loading} />
        { this.state.name &&
            <InfoGroup title={this.state.name} titleChangeable={true} onTitleChange={e => this.setState({name: e})} onSave={e => this.saveName()} >
                { !this.state.accessible &&
                    <div className="automation-device-retry-connection">No connection to the device could be made. <span onClick={e => this.retryConnection()}>Retry</span></div>
                }
                { this.state.device_type === "Light" &&
                    <div className="automation-device-light">
                        <div className="automation-device-state"><Switch value={this.state.on} onToggle={(value) => this.toggleLight(value)} /></div>

                        { (this.state.can_dim || this.state.can_change_warmth) &&
                            <div className="device-group-controls">
                                { this.state.can_dim &&
                                 <div className="light-group-dimmer">
                                    <Slider format={this.writePercentage} formatMinMax={(value) => value === 0 ? "Dimmer": "" } min={0} max={100} value={this.state.dim} onChange={(value) => this.lightDimmerChange(value)} />
                                </div>
                                }
                                { this.state.can_change_warmth &&
                                    <div className="light-group-warmth">
                                        <Slider format={this.writePercentage} formatMinMax={(value) => value === 0 ? "Warmth": "" } min={0} max={100} value={this.state.warmth} onChange={(value) => this.lightWarmthChange(value)} />
                                    </div>
                                }
                            </div>
                        }
                    </div>
                }
                { this.state.device_type === "Thermostat" &&
                    <div>
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
                                    <div className="heating-increase-temp" onClick={() => this.changeTemperature(1)}>+</div>
                                    <div className="heating-decrease-temp" onClick={() => this.changeTemperature(-1)}>-</div>
                                </div>
                            </div>
                        </div>
                    </div>
                }


                { this.state.historyData && this.state.historyData.length > 1 &&
                    <InfoGroup title="History">
                        { this.state.historyDataType === "temperature" &&
                            <ResponsiveContainer width="100%" height={200}>
                                <LineChart data={this.state.historyData} margin={{top:20,right:30,bottom:30,left:-10}}>
                                  <XAxis angle={20}
                                         dy={20}
                                         interval="preserveStartEnd"
                                         dataKey="timestamp"
                                         tickFormatter = {(timestamp) => formatTime(timestamp, false, true, true, true, true)}
                                         />
                                  <YAxis dataKey="value" type="number" domain={['dataMin - 2', 'dataMax + 2']}/>
                                  <Line dataKey="value" stroke="#8884d8" dot={false} animationDuration={500} />
                                  <Tooltip content={<CustomTooltip />} />
                                </LineChart>
                            </ResponsiveContainer>
                         }

                         { (this.state.historyDataType === "active" || this.state.historyDataType === "on") &&
                             <ResponsiveContainer width="100%" height={200}>
                                <LineChart data={this.state.historyData} margin={{top:20,right:30,bottom:30,left:-10}}>
                                  <XAxis angle={20}
                                         dy={20}
                                         interval="preserveStartEnd"
                                         dataKey="timestamp"
                                         tickFormatter = {(timestamp) => formatTime(timestamp, false, true, true, true, true)}
                                         />
                                  <YAxis dataKey="value" reversed type="category"/>
                                  <Line dataKey="value" fill="#8884d8" animationDuration={500}/>
                                  <Tooltip content={<CustomTooltip />} />
                                </LineChart>
                            </ResponsiveContainer>
                         }
                    </InfoGroup>
                }
            </InfoGroup>

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
				<div>{payload[0].value}</div>
				<div className="desc">
				{ payload[0].payload.source === "user" && <span>Set by user</span> }
				{ payload[0].payload.source === "rule" && <span>Set by rule</span> }
				</div>
			</div>
		);
	}

	return null;
};

export default AutomationDeviceView;