import React, { Component } from 'react';
import axios from 'axios';

import Widget from './Widget.js';

class TempWidget extends Component {
  constructor(props) {
    super(props);

    this.state = {};
    this.getSize = this.getSize.bind(this);
    this.changeTemp = this.changeTemp.bind(this);
  }


  getSize(){
    return {width: 120, height: 135};
  }

  componentDidMount() {
    axios.get(window.vars.apiBase + 'toon').then(
        (data) => {
            this.setState({thermostatData: data.data});
            console.log(data.data);
         },
        (error) => { console.log(error) }
    )
  }

  componentWillUnmount(){
  }

  formatTemperature(value){
     return (Math.round(value / 10) / 10) + "°C";
  }

  changeTemp(delta){
    var newTemp = this.state.thermostatData.current_setpoint + delta;
    var old = this.state.thermostatData;
    old.current_setpoint = newTemp;
    this.setState({thermostatData: old});

    axios.post(window.vars.apiBase + 'toon/temperature?temperature=' + newTemp).then(
        (data) => {
            console.log(data);
         },
        (error) => { console.log(error) }
    )
  }

  render() {
    return (
      <Widget {...this.props} loading={!this.state.thermostatData}>
      { this.state.thermostatData &&
            <div className="temp-widget-content">
                <div className="temp-widget-current-temp">
                    <div className="temp-widget-current-header">current</div>
                    <div className="temp-widget-current-value">{this.formatTemperature(this.state.thermostatData.current_display_temp)}</div>
                </div>
                <div className="temp-widget-set-temp">
                    <div className="temp-widget-current-setpoint-header">target</div>
                    <div className="temp-widget-decrease-temp" onClick={() => this.changeTemp(-50)}>-</div>
                    <div className="temp-widget-current-setpoint">{this.formatTemperature(this.state.thermostatData.current_setpoint)}</div>
                    <div className="temp-widget-increase-temp" onClick={() => this.changeTemp(50)}>+</div>
                </div>
            </div>
         }
      </Widget>
    );
  }
};

export default TempWidget;