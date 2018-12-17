import React, { Component } from 'react';
import Widget from './../Widget'
import Socket from './../../../Socket.js'
import Button from './../../Components/Button'
import axios from 'axios'

class MediaPlayerWidget extends Component {
  constructor(props) {
    super(props);
    this.state = {playerData: {}, mediaData: {}};
    this.playerUpdate = this.playerUpdate.bind(this);
    this.mediaUpdate = this.mediaUpdate.bind(this);
    this.testClick = this.testClick.bind(this);
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

  testClick() {
    axios.post('http://localhost/hd/play_file?instance='+this.props.instance + "&path=C:/jellies.mp4&position=0");
  }
  stopClick() {
    axios.post('http://localhost/player/stop_player?instance='+this.props.instance);
  }

  render() {
    const playerData = this.state.playerData;
    const mediaData = this.state.mediaData;
    const instance = this.props.instance;

    let mediaWidget;
    if (mediaData.title){
        mediaWidget =
        <div className="mediaplayer-widget">
            <div className="mediaplayer-widget-controls">
                <div className="mediaplayer-widget-control">Pause/play</div>
                <div className="mediaplayer-widget-control">Stop</div>
            </div>
            <div className="mediaplayer-widget-info">
                <div className="mediaplayer-widget-info-title">{mediaData.title}</div>
                <div className="mediaplayer-widget-info-time">{playerData.playing_for}</div>
            </div>
        </div>;
    }
    else{
        mediaWidget = <div className="mediaplayer-widget-not-playing">Nothing playing</div>;
    }

    return (
      <Widget title={"Mediaplayer " + instance}>
            {mediaWidget}
            <br/>
          <Button text="Test play" onClick={this.testClick} />
          <Button text="Test stop" onClick={this.stopClick} />
      </Widget>
    );
  }
};

export default MediaPlayerWidget;