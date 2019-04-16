import React, { Component } from 'react';

import DashboardLink from './../../Components/DashboardLink'
import heatingImg from './../../../Images/heating.svg'
import lightingImg from './../../../Images/bulb.svg'
import deviceImg from './../../../Images/device.svg'
import rulesImg from './../../../Images/rules.svg'

class HomeDashboardView extends Component {
  constructor(props) {
    super(props);
    this.props.functions.changeBack({});
    this.props.functions.changeTitle("Home automation");
    this.props.functions.changeRightImage(null);
  }

  componentDidMount() {
  }

  render() {
    return (
    <div className="mediaplayer-dashboard">
        <DashboardLink to="/home/heating" img={heatingImg} text="heating"></DashboardLink>
        <DashboardLink to="/home/lighting" img={lightingImg} text="lighting"></DashboardLink>
        <DashboardLink to="/home/devices" img={deviceImg} text="devices"></DashboardLink>
        <DashboardLink to="/home/rules" img={rulesImg} text="rules"></DashboardLink>
    </div>
    );
  }
};

export default HomeDashboardView;