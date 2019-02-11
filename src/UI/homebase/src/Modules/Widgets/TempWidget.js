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
    return {width: 120, height: 50};
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

  render() {
    return (
      <Widget {...this.props}>
        <div className="temp-widget-current-temp">current: {this.state.thermostatData.current_display_temp}</div>
        <div className="temp-widget-set-temp">setpoint: {this.state.thermostatData.current_setpoint}</div>
      </Widget>
    );
  }
};

export default TestWidget;