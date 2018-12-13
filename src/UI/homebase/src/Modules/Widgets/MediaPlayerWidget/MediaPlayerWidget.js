import React, { Component } from 'react';
import Widget from './../Widget'
import Socket from './../../../Socket.js'
import Button from './../../Components/Button'

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
    Socket.request("play_file", [this.props.instance, "C:/jellies.mp4"]);
  }
  stopClick() {
    Socket.request("play_stop", [this.props.instance]);
  }

  render() {
    const playerData = this.state.playerData;
    const mediaData = this.state.mediaData;
    const instance = this.props.instance;
    return (
      <Widget>
          {instance}<br />
          {mediaData.type}: {mediaData.title}<br />
          {playerData.playing_for}
          <Button text="Test play" onClick={this.testClick} />
          <Button text="Test stop" onClick={this.stopClick} />
      </Widget>
    );
  }
};

export default MediaPlayerWidget;