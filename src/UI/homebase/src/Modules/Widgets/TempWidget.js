import React, { Component } from 'react';
import { Link } from "react-router-dom";
import axios from 'axios';

import Widget from './Widget.js';

class TestWidget extends Component {
  constructor(props) {
    super(props);

    this.state = {thermostatData: {}};
    this.getSize = this.getSize.bind(this);
  }


  getSize(){
    return {width: 80, height: 80};
  }

  componentDidMount() {
    axios.get('http://'+window.location.hostname+'/toon/get_status').then(
        (data) => {
            this.setState({thermostatData: data.data});
            console.log(data);
         },
        (error) => { console.log(error) }
    )
  }

  componentWillUnmount(){
  }

  formatTemperature(value){
     return (Math.round(value / 10) / 10) + "°C";
  }

  render() {
    return (
      <Widget {...this.props}>
        <div className="temp-widget-content">
            <div className="temp-widget-current-temp">{this.formatTemperature(this.state.thermostatData.current_display_temp)}</div>
            <div className="temp-widget-set-temp">
                <div className="temp-widget-decrease-temp">-</div>
                <div className="temp-widget-current-setpoint">{this.formatTemperature(this.state.thermostatData.current_setpoint)}</div>
                <div className="temp-widget-increase-temp">+</div>
            </div>
        </div>
      </Widget>
    );
  }
};

export default TestWidget;