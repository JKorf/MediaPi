import React, { Component } from 'react';
import axios from 'axios'

import View from './../View'
import MediaPlayerWidget from './../../Widgets/MediaPlayerWidget'
import Button from './../../Components/Button'

class DashboardView extends Component {
  constructor(props) {
    super(props);
  }

  btnClick() {
    axios.post('http://localhost/hd/play_file?instance=Woonkamer&path=C:/jellies.mp4');
  }

  btn2Click() {
    axios.post('http://localhost/hd/play_file?instance=Slaapkamer&path=C:/jellies.mp4');
  }

  render() {
    return (
      <View>
              <Button text="TestMaster" onClick={this.btnClick} />
              <Button text="TestSlave" onClick={this.btn2Click} />

        <MediaPlayerWidget instance="Woonkamer"/>
        <MediaPlayerWidget instance="Slaapkamer"/>
      </View>
    );
  }
};

export default DashboardView;