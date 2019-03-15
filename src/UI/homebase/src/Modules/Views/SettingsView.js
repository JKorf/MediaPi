import React, { Component } from 'react';
import axios from 'axios';
import Socket from './../../Socket2.js';

import { InfoGroup } from './../Components/InfoGroup'
import ViewLoader from './../Components/ViewLoader';

class SettingsView extends Component {
  constructor(props) {
    super(props);

    this.state = {};

    this.props.functions.changeBack({});
    this.props.functions.changeTitle("Settings");
    this.props.functions.changeRightImage(null);
  }

  componentDidMount() {
  }

  componentWillUnmount() {
  }

  render() {
    return <div className="settings-view">
        <InfoGroup title="Appearance">
            Test
        </InfoGroup>
    </div>
  }
};

export default SettingsView;