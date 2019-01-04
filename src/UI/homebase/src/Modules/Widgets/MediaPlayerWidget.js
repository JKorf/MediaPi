import React, { Component } from 'react';
import Widget from './Widget.js';
import Socket from './../../Socket.js';
import Button from './../Components/Button';
import SvgImage from './../Components/SvgImage';
import MediaProgress from './../Components/MediaProgress';
import Popup from './../Components/Popups/Popup.js';
import axios from 'axios';

import playImage from './../../Images/play.svg';
import pauseImage from './../../Images/pause.svg';
import stopImage from './../../Images/stop.svg';

class MediaPlayerWidget extends Component {
  constructor(props) {
    super(props);
    this.state = {playerData: {}, mediaData: {}, loading: false};
    this.playerUpdate = this.playerUpdate.bind(this);
    this.mediaUpdate = this.mediaUpdate.bind(this);

    this.pausePlayClick = this.pausePlayClick.bind(this);
    this.stopClick = this.stopClick.bind(this);
  }

  componentDidMount() {
    this.playerSub = Socket.subscribe(this.props.instance + ".player", this.playerUpdate);
    this.mediaSub = Socket.subscribe(this.props.instance + ".media", this.mediaUpdate);
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

  pausePlayClick(){
    this.setState({loading: true});
    axios.post('http://localhost/player/pause_resume_player?instance=' + this.props.id)
    .then(
        () => this.setState({loading: false}),
        ()=> this.setState({loading: false})
    );
    const playerData = this.state.playerData;
    playerData.state = (playerData.state == 3 ? 4: 3);
    this.setState({playerData: playerData});
  }

  stopClick(){
    this.setState({loading: true});
    axios.post('http://localhost/player/stop_player?instance=' + this.props.id)
    .then(
        () => this.setState({loading: false}),
        ()=> this.setState({loading: false})
    );
  }

  render() {
    const playerData = this.state.playerData;
    const mediaData = this.state.mediaData;
    const instance = this.props.instance;
    const loading = this.state.loading;

    let mediaWidget;
    if (mediaData.title){
        let playPauseButton = <SvgImage key={playerData.state} src={pauseImage} />
        if (playerData.state === 4)
            playPauseButton = <SvgImage key={playerData.state} src={playImage} />

        mediaWidget =
        <div className="mediaplayer-widget">
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
            <MediaProgress percentage={playerData.playing_for / playerData.length * 100} ></MediaProgress>
            { loading &&
                <Popup loading={loading} />
            }
        </div>;
    }
    else{
        mediaWidget = <div className="mediaplayer-widget-not-playing">Nothing playing</div>;
    }

    return (
      <Widget title={"Mediaplayer " + instance}>
          {mediaWidget}
      </Widget>
    );
  }
};

export default MediaPlayerWidget;