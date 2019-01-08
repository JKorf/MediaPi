import React, { Component } from 'react';
import axios from 'axios';

import View from './../View.js';
import MediaPlayerView from './MediaPlayerView.js'
import Socket from './../../../Socket.js';

import Button from './../../Components/Button';
import Slider from './../../Components/Slider';
import SelectInstancePopup from './../../Components/Popups/SelectInstancePopup'
import Popup from './../../Components/Popups/Popup'
import { InfoGroup, InfoRow } from './../../Components/InfoGroup'

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

  writeSize(value){
    if (value < 1000)
        return value + "b";
    if (value < 1000 * 1000)
        return Math.round(value / 1000) + "kb";
    if (value < 1000 * 1000 * 1000)
        return Math.round(value / (1000 * 1000) * 100) / 100 + "mb";
    return Math.round(value / (1000 * 1000 * 1000) * 100) / 100 + "gb";
  }

  writeSpeed(value)
  {
    return this.writeSize(value) + "ps";
  }

  render() {

    let torrentComponent = "";
    if (this.state.torrentData.title)
        torrentComponent = (
            <InfoGroup title="Torrent">
                <InfoRow name="Torrent name" value={this.state.torrentData.title} />
                <InfoRow name="Media name" value={this.state.torrentData.media_file} />
                <InfoRow name="Downloaded" value={this.writeSize(this.state.torrentData.downloaded)} />
                <InfoRow name="Left" value={this.writeSize(this.state.torrentData.left)} />
                <InfoRow name="Size" value={this.writeSize(this.state.torrentData.size)} />
                <InfoRow name="Speed" value={this.writeSpeed(this.state.torrentData.download_speed)} />
            </InfoGroup>
        )

    return (
        <div className="player-details">
            <InfoGroup title="Media">
                <div className="player-details-img"><img src={this.state.mediaData.image} /></div>
                <div className="player-details-media">
                    <div className="player-details-title">{this.state.mediaData.title}</div>
                    <div className="player-details-slider"><Slider min={0} max={this.state.playerData.length / 1000} value={this.state.playerData.playing_for / 1000} /></div>
                    <InfoRow name="State" value={this.state.playerData.state} />
                    <InfoRow name="Volume" value={this.state.playerData.volume} />
                    <InfoRow name="Subtitle delay" value={this.state.playerData.sub_delay} />
                </div>


            </InfoGroup>

             {torrentComponent}

            <InfoGroup title="State">
                <InfoRow name="CPU" value={this.state.stateData.cpu + "%"} />
                <InfoRow name="Memory" value={this.state.stateData.memory + "%"} />
                <InfoRow name="Threads" value={this.state.stateData.threads} />
            </InfoGroup>
        </div>
    );
  }
};

export default PlayerView;