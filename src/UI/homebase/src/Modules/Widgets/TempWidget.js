import React, { Component } from 'react';
import axios from 'axios';

import Widget from './Widget.js';
import Socket from './../../Socket2.js';

class TempWidget extends Component {
  constructor(props) {
    super(props);

    this.state = {loading: true};
    this.getSize = this.getSize.bind(this);
    this.changeTemp = this.changeTemp.bind(this);
    this.devicesUpdate = this.devicesUpdate.bind(this);
  }

  shouldShow(){
    return true;
  }


  getSize(){
    return {width: 180, height: 135};
  }

  componentDidMount() {
      this.devicesSub = Socket.subscribe("device:ToonThermostat", this.devicesUpdate);
  }

  componentWillUnmount(){
      Socket.unsubscribe(this.devicesSub);
  }

  devicesUpdate(subId, data){
    this.setState(data);
    this.setState({loading: false});
  }

  formatTemperature(value){
     return value + "°C";
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
    return (
      <Widget {...this.props} loading={this.state.loading}>
        <div className="temp-widget-content">
            <div className="temp-widget-current-temp">
                <div className="temp-widget-current-header">current</div>
                <div className="temp-widget-current-value">{this.formatTemperature(this.state.temperature)}</div>
            </div>
            <div className="temp-widget-set-temp">
                <div className="temp-widget-current-setpoint-header">target</div>
                <div className="temp-widget-decrease-temp" onClick={() => this.changeTemp(-1)}>-</div>
                <div className="temp-widget-current-setpoint">{this.formatTemperature(this.state.setpoint)}</div>
                <div className="temp-widget-increase-temp" onClick={() => this.changeTemp(1)}>+</div>
            </div>
        </div>
      </Widget>
    );
  }
};

export default TempWidget;