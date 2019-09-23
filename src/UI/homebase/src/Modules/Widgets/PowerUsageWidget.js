import React, { Component } from 'react';

import Widget from './Widget.js';
import UsageGraph from './../Components/UsageGraph';

class PowerUsageWidget extends Component {
  constructor(props) {
    super(props);

    this.state = {};
    this.getSize = this.getSize.bind(this);

    this.endTime = this.floorDate(new Date(), 60 * 60 * 1000).getTime();
    this.startTime = this.endTime - 8 * 60 * 60 * 1000;
  }

  floorDate(date, period) {
    return new Date(Math.floor(date.getTime() / period ) * period);
  }

  shouldShow(){
    return true;
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
          <UsageGraph type="power" startTime={this.startTime} endTime={this.endTime} interval={"hours"}  height={184} />
      </Widget>
    );
  }
};

export default PowerUsageWidget;