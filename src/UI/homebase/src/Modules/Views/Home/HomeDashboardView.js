import React, { Component } from 'react';

import DashboardLink from './../../Components/DashboardLink'
import gasImg from './../../../Images/heating.svg'
import tempImg from './../../../Images/thermometer.svg'
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
        <DashboardLink to="/home/tradfri" img={lightingImg} text="lights & sockets"></DashboardLink>
        <DashboardLink to="/home/heating" img={tempImg} text="heating"></DashboardLink>

        <DashboardLink to="/home/gas" img={gasImg} text="gas usage"></DashboardLink>
        <DashboardLink to="/home/power" img={gasImg} text="power usage"></DashboardLink>

        <DashboardLink to="/home/devices" img={deviceImg} text="devices"></DashboardLink>
        <DashboardLink to="/home/rules" img={rulesImg} text="rules"></DashboardLink>
    </div>
    );
  }
};

export default HomeDashboardView;