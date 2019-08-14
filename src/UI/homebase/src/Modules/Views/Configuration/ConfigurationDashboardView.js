import React, { Component } from 'react';

import DashboardLink from './../../Components/DashboardLink'
import testImg from './../../../Images/settings.svg'
import lockImg from './../../../Images/locked.svg'

class ConfigurationDashboardView extends Component {
  constructor(props) {
    super(props);

    this.state = {};

    this.props.functions.changeBack({});
    this.props.functions.changeTitle("Configuration");
    this.props.functions.changeRightImage(null);
  }

  componentDidMount() {
  }

  componentWillUnmount() {
  }

  render() {
    return <div className="settings-view">
        <DashboardLink to="/configuration/access" img={lockImg} text="Access"></DashboardLink>
        <DashboardLink to="/configuration/test" img={testImg} text="Test"></DashboardLink>
    </div>
  }
};

export default ConfigurationDashboardView;