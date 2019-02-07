import React, { Component } from 'react';
import { Link } from "react-router-dom";

import Widget from './Widget.js';
import Socket from './../../Socket.js';
import Button from './../Components/Button';
import SvgImage from './../Components/SvgImage';
import MediaProgress from './../Components/MediaProgress';
import Popup from './../Components/Popups/Popup.js';
import StopPopup from './../Components/Popups/StopPopup.js';
import axios from 'axios';

import playImage from './../../Images/play.svg';
import pauseImage from './../../Images/pause.svg';
import stopImage from './../../Images/stop.svg';

class MediaPlayerWidget extends Component {
  constructor(props) {
    super(props);
    this.states = ["loading", "nothing", "confirmStop"];
    this.state = {playerData: {}, mediaData: {}, slaveData: [], state: this.states[1]};

    this.slaveUpdate = this.slaveUpdate.bind(this);
    this.getSize = this.getSize.bind(this);
  }

  componentDidMount() {
    this.slaveSub = Socket.subscribe("slaves", this.slaveUpdate);
  }

  componentWillUnmount(){
    Socket.unsubscribe(this.slaveSub);
  }

  getSize()
  {
    return {width: 200,  height: 34 + this.state.slaveData.length * 59};
  }

  slaveUpdate(data){
    this.setState({slaveData: data});
    this.props.updateFunc();
  }

  render() {
    const slaves = this.state.slaveData;
    const style = {
        height: "calc(100% / " + slaves.length + ")"
    };

    return (
        <Widget {...this.props}>
            <div className="mediaplayer-widget-holder">
            {
                slaves.map((slave, index) => <div style={style} className="mediaplayer-widget-item" key={slave.id}><MediaPlayerWidgetInstance showPopup={this.props.showPopup} closePopup={this.props.closePopup} instance={slave} /></div>)
            }
            </div>
      </Widget>
    );
  }
};

class MediaPlayerWidgetInstance extends Component {
  constructor(props) {
    super(props);
    this.states = ["loading", "nothing", "confirmStop"];
    this.state = {playerData: {}, mediaData: {}, state: this.states[1]};
    this.playerUpdate = this.playerUpdate.bind(this);
    this.mediaUpdate = this.mediaUpdate.bind(this);

    this.pausePlayClick = this.pausePlayClick.bind(this);
    this.confirmStop = this.confirmStop.bind(this);
    this.cancelStop = this.cancelStop.bind(this);
    this.stopClick = this.stopClick.bind(this);
  }

  componentDidMount() {
    this.playerSub = Socket.subscribe(this.props.instance.id + ".player", this.playerUpdate);
    this.mediaSub = Socket.subscribe(this.props.instance.id + ".media", this.mediaUpdate);
  }

  componentWillUnmount(){
    Socket.unsubscribe(this.playerSub);
    Socket.unsubscribe(this.mediaSub);
  }

  playerUpdate(data){
    this.setState({playerData: data});
  }
  mediaUpdate(data){
    this.setState({mediaData: data});
  }

  pausePlayClick(e){
    this.setState({state: this.states[0]});
    e.preventDefault();

    axios.post('http://localhost/play/pause_resume_player?instance=' + this.props.instance.id)
    .then(
        () => this.setState({state: this.states[1]}),
        ()=> this.setState({state: this.states[1]})
    );
    const playerData = this.state.playerData;
    playerData.state = (playerData.state == 3 ? 4: 3);
    this.setState({playerData: playerData});
  }

  stopClick(e){
    this.stopPopup = <StopPopup title={this.state.mediaData.title} onCancel={this.cancelStop} onConfirm={this.confirmStop} />;
    this.props.showPopup(this.stopPopup);
    e.preventDefault();
  }

  cancelStop(){
    this.props.closePopup(this.stopPopup);
  }

  confirmStop(e){
    this.props.closePopup(this.stopPopup);
    this.setState({state: this.states[1]});
    axios.post('http://localhost/play/stop_player?instance=' + this.props.instance.id )
    .then(
        () => this.setState({state: this.states[0]}),
        ()=> this.setState({state: this.states[0]})
    );
  }

  render() {
    const playerData = this.state.playerData;
    const mediaData = this.state.mediaData;
    const instance = this.props.instance;
    const state = this.state.state;

    let percentagePlaying = playerData.playing_for / playerData.length * 100;
    if (playerData.length == 0 && playerData.playing_for != 0)
        percentagePlaying = 100;

    let mediaWidget = "Nothing playing";
    if (mediaData.title)
    {
        let playPauseButton = <SvgImage key={playerData.state} src={pauseImage} />
        if (playerData.state === 4)
            playPauseButton = <SvgImage key={playerData.state} src={playImage} />

        mediaWidget =
        <div className="mediaplayer-widget-content">
            <div className="mediaplayer-widget-info">
                <div className="mediaplayer-widget-info-title truncate">{mediaData.title}</div>
            </div>
            <div className="mediaplayer-widget-controls">
                <div className="mediaplayer-widget-control" onClick={this.pausePlayClick}>
                    {playPauseButton}
                </div>
                <div className="mediaplayer-widget-control" onClick={this.stopClick}>
                     <SvgImage src={stopImage} />
                </div>
            </div>
            <MediaProgress percentage={percentagePlaying} ></MediaProgress>

        </div>

    }

    return (<div className={"mediaplayer-widget " + (mediaData.title ? "": "not-playing")} >
            <Link to={"/mediaplayer/player/" + instance.id} key={instance.id}>
                <div className="mediaplayer-name">{instance.name}</div>
                <div className="mediaplayer-playing ">
                    {mediaWidget}
                </div>
            </Link>
        </div>);
  }
};

export default MediaPlayerWidget;