import React, { Component } from 'react';

import { InfoGroup } from './../Components/InfoGroup'

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
        <InfoGroup title=".">

        </InfoGroup>
    </div>
  }
};

export default SettingsView;