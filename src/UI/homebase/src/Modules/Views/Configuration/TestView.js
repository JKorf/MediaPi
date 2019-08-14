import React, { Component } from 'react';
import axios from 'axios';

import { InfoGroup } from './../../Components/InfoGroup'
import Button from './../../Components/Button'

class ConfigurationDashboardView extends Component {
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

  testShelly(on){
    axios.post(window.vars.apiBase + 'util/shelly?ip=' + this.state.ip + "&state=" + on);
  }

  render() {
    return <div className="settings-view">
        <InfoGroup title="Shelly">
            <div className="settings-info-group">
                <input type="text" placeholder="ip address" onChange={(e) => this.setState({ip:e.target.value})} />
                <div className="settings-button">
                    <Button text="Shelly on" onClick={() => this.testShelly(true)}/>
                    <Button text="Shelly off" onClick={() => this.testShelly(false)}/>
                </div>
            </div>
        </InfoGroup>
    </div>
  }
};

export default ConfigurationDashboardView;