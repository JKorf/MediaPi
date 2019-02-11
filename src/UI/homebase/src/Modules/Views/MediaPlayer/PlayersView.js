import React, { Component } from 'react';
import { Link } from "react-router-dom";
import axios from 'axios';

import Socket from './../../../Socket.js';
import MediaPlayerView from './MediaPlayerView.js'

import Button from './../../Components/Button';
import MediaProgress from './../../Components/MediaProgress';
import SelectInstancePopup from './../../Components/Popups/SelectInstancePopup'
import Popup from './../../Components/Popups/Popup'

class PlayersView extends Component {
  constructor(props) {
    super(props);
    this.state = {slaveData: []};

    this.props.functions.changeBack({to: "/mediaplayer/" });
    this.props.functions.changeTitle("Players");
    this.props.functions.changeRightImage(null);

    this.slaveUpdate = this.slaveUpdate.bind(this);
  }

  componentDidMount() {
      this.slaveSub = Socket.subscribe("slaves", this.slaveUpdate);
  }

  componentWillUnmount() {
    Socket.unsubscribe(this.slaveSub);
  }

  slaveUpdate(subId, data){
    this.setState({slaveData: data});
  }

  render() {
    const slaves = this.state.slaveData;

    return (
        slaves.map((slave, index) => <Link to={"/mediaplayer/player/" + slave.id} key={slave.id}>
            <PlayerInstance instance={slave} />
        </Link>)
    );
  }
};

class PlayerInstance extends Component {
  constructor(props) {
    super(props);
    this.state = {playerData: {}, mediaData: {}};
    this.playerUpdate = this.playerUpdate.bind(this);
    this.mediaUpdate = this.mediaUpdate.bind(this);
  }

  componentDidMount() {
    this.playerSub = Socket.subscribe(this.props.instance.id + ".player", this.playerUpdate);
    this.mediaSub = Socket.subscribe(this.props.instance.id + ".media", this.mediaUpdate);
  }

  componentWillUnmount(){
    Socket.unsubscribe(this.playerSub);
    Socket.unsubscribe(this.mediaSub);
  }

  playerUpdate(subId, data){
    this.setState({playerData: data});
  }
  mediaUpdate(subId, data){
    this.setState({mediaData: data});
  }

  render() {
    const playerData = this.state.playerData;
    const mediaData = this.state.mediaData;
    const instance = this.props.instance;

    let percentagePlaying = playerData.playing_for / playerData.length * 100;
    if (playerData.length == 0 && playerData.playing_for != 0)
        percentagePlaying = 100;

    let mediaWidget;
    if (mediaData.title){
        mediaWidget =
        <div className="mediaplayer-widget">
            <div className="mediaplayer-widget-info">
                <div className="mediaplayer-widget-info-title truncate">{mediaData.title}</div>
            </div>
            <MediaProgress percentage={percentagePlaying} ></MediaProgress>
        </div>;
    }
    else{
        mediaWidget = <div className="mediaplayer-widget-not-playing">Nothing playing</div>;
    }

    return (
        <div className="player-instance">
            <div className="player-instance-title">{instance.name}</div>
            <div className="player-instance-content">{mediaWidget}</div>
          </div>
    );
  }
};

export default PlayersView;