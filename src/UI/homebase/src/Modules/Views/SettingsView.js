import React, { Component } from 'react';
import axios from 'axios';

import { InfoGroup } from './../Components/InfoGroup'

class SettingsView extends Component {
  constructor(props) {
    super(props);

    this.props.functions.changeBack({});
    this.props.functions.changeTitle("Settings");
    this.props.functions.changeRightImage(null);
  }

  componentDidMount() {
  }

  componentWillUnmount() {
  }

  debugLogging(){
    axios.post(window.vars.apiBase + 'util/log')
  }

  render() {
    return <div className="settings-view">
        <InfoGroup title="Appearance">
            Test
        </InfoGroup>
        <input type="button" value="Debug logging" onClick={() => this.debugLogging()}/>
    </div>
  }
};

export default SettingsView;