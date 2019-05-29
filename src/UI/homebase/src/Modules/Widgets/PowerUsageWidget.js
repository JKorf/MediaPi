import React, { Component } from 'react';
import { Link } from "react-router-dom";
import axios from 'axios';

import Widget from './Widget.js';
import PowerUsageGraph from './../Components/PowerUsageGraph';

class PowerUsageWidget extends Component {
  constructor(props) {
    super(props);

    this.state = {};
    this.getSize = this.getSize.bind(this);
  }


  getSize(){
     return {width: 250, height: 34 + 150};
  }

  componentDidMount() {

  }

  componentWillUnmount(){
  }

  render() {
    return (
      <Widget {...this.props} loading={false}>
          <PowerUsageGraph hoursAgo={0} height={184} />
      </Widget>
    );
  }
};

export default PowerUsageWidget;