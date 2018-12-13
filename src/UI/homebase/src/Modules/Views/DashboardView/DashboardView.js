import React, { Component } from 'react';
import axios from 'axios'

import View from './../View'
import MediaPlayerWidget from './../../Widgets/MediaPlayerWidget'
import Button from './../../Components/Button'
import Socket from './../../../Socket.js'

class DashboardView extends Component {
  constructor(props) {
    super(props);
    this.state = {slaveData: []}

    this.slaveUpdate = this.slaveUpdate.bind(this);
  }

  componentDidMount() {
      this.slaveSub = Socket.subscribe("slaves", this.slaveUpdate);
  }

  slaveUpdate(data){
    this.setState({slaveData: data});
  }

  btnClick() {
    Socket.request("play_file", ["Woonkamer", "C:/jellies.mp4"]);
  }

  btn2Click() {
    Socket.request("play_file", ["Slaapkamer", "C:/jellies.mp4"]);
  }

  render() {
    const slaves = this.state.slaveData;
    return (
      <View>
              <Button text="TestMaster" onClick={this.btnClick} />
              <Button text="TestSlave" onClick={this.btn2Click} />
        {
            slaves.map((slave, index) => <MediaPlayerWidget key={index} instance={slave.name} />)
        }
      </View>
    );
  }
};

export default DashboardView;