import React, { Component } from 'react';
import axios from 'axios'

import View from './View.js'
import MediaPlayerWidget from './../Widgets/MediaPlayerWidget.js'
import Socket from './../../Socket.js'

class DashboardView extends Component {
  constructor(props) {
    super(props);
    this.state = {slaveData: []}
    this.props.changeBack({});
    this.props.changeTitle("Home base");

    this.slaveUpdate = this.slaveUpdate.bind(this);
  }

  componentDidMount() {
      this.slaveSub = Socket.subscribe("slaves", this.slaveUpdate);
  }

  componentWillUnmount() {
    Socket.unsubscribe(this.slaveSub);
  }

  slaveUpdate(data){
    this.setState({slaveData: data});
  }

  render() {
    const slaves = this.state.slaveData;
    return (
    <div className="view-wrapper">
      <View>
        {
            slaves.map((slave, index) => <MediaPlayerWidget key={slave.id} id={slave.id} instance={slave} />)
        }
      </View>
      </div>
    );
  }
};

export default DashboardView;