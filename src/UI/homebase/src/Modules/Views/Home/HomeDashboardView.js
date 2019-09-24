import React, { Component } from 'react';

import DashboardLink from './../../Components/DashboardLink'
import gasImg from './../../../Images/heating.svg'
import tempImg from './../../../Images/thermometer.svg'
import lightingImg from './../../../Images/bulb.svg'
import deviceImg from './../../../Images/device.svg'
import rulesImg from './../../../Images/rules.svg'
import powerImg from './../../../Images/power.svg'
import smartHomeImg from './../../../Images/smart-home.svg'
import moodsImg from './../../../Images/moods.svg'

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
        <DashboardLink to="/home/gas" img={gasImg} text="gas usage"></DashboardLink>
        <DashboardLink to="/home/power" img={powerImg} text="power usage"></DashboardLink>

        <DashboardLink to="/home/devices" img={deviceImg} text="devices"></DashboardLink>
        <DashboardLink to="/home/rules" img={rulesImg} text="rules"></DashboardLink>

        <DashboardLink to="/home/automation" img={smartHomeImg} text="automation"></DashboardLink>

        <DashboardLink to="/home/moods" img={moodsImg} text="moods"></DashboardLink>
    </div>
    );
  }
};

export default HomeDashboardView;