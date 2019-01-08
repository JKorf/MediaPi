import React, { Component } from 'react';
import axios from 'axios';

import View from './../View.js';
import MediaPlayerView from './MediaPlayerView.js'
import Socket from './../../../Socket.js';

import Button from './../../Components/Button';
import SelectInstancePopup from './../../Components/Popups/SelectInstancePopup'
import Popup from './../../Components/Popups/Popup'

class PlayerView extends Component {
  constructor(props) {
    super(props);
    this.props.changeBack({to: "/mediaplayer/players/" });

    this.changedTitle = false;
    this.state = {playerData: {}, mediaData: {}, torrentData: {}, stateData: {}};

    this.playerUpdate = this.playerUpdate.bind(this);
    this.mediaUpdate = this.mediaUpdate.bind(this);
    this.torrentUpdate = this.torrentUpdate.bind(this);
    this.stateUpdate = this.stateUpdate.bind(this);
  }

  componentDidMount() {
    this.stateSub = Socket.subscribe(this.props.match.params.id + ".state", this.stateUpdate);
    this.playerSub = Socket.subscribe(this.props.match.params.id + ".player", this.playerUpdate);
    this.mediaSub = Socket.subscribe(this.props.match.params.id + ".media", this.mediaUpdate);
    this.torrentSub = Socket.subscribe(this.props.match.params.id + ".torrent", this.torrentUpdate);
  }

  componentWillUnmount(){
    Socket.unsubscribe(this.stateUpdate);
    Socket.unsubscribe(this.playerSub);
    Socket.unsubscribe(this.mediaSub);
    Socket.unsubscribe(this.torrentSub);
  }

  stateUpdate(data){
    if(!this.changedTitle)
    {
        this.changedTitle = true;
        this.props.changeTitle(data.name);
    }
    this.setState({stateData: data});
  }
  playerUpdate(data){
    this.setState({playerData: data});
  }
  mediaUpdate(data){
    this.setState({mediaData: data});
  }
  torrentUpdate(data){
    this.setState({torrentData: data});
  }

  render() {

    return (
        <div>Player!</div>
    );
  }
};

export default PlayerView;