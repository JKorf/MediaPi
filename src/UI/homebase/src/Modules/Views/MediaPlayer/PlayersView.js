import React, { Component } from 'react';
import { Link } from "react-router-dom";
import axios from 'axios';

import Socket from './../../../Socket.js';
import MediaPlayerView from './MediaPlayerView.js'

import Button from './../../Components/Button';
import SelectInstancePopup from './../../Components/Popups/SelectInstancePopup'
import Popup from './../../Components/Popups/Popup'

class PlayersView extends Component {
  constructor(props) {
    super(props);
    this.state = {slaveData: []};

    this.props.changeBack({to: "/mediaplayer/" });
    this.props.changeTitle("Players");

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

  selectSlave(slave)
  {
  }

  render() {
    const slaves = this.state.slaveData;


    return (
        slaves.map((slave, index) => <Link to={"/mediaplayer/player/" + slave.id} key={slave.id}><div className="player" >{slave.name}</div></Link>)
    );
  }
};

export default PlayersView;