import React, { Component } from 'react';

import Widget from './Widget.js';
import UsageGraph from './../Components/UsageGraph';

class PowerUsageWidget extends Component {
  constructor(props) {
    super(props);

    this.state = {};
    this.getSize = this.getSize.bind(this);
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
          <UsageGraph hoursAgo={0} height={184} />
      </Widget>
    );
  }
};

export default PowerUsageWidget;