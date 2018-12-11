import React, { Component } from 'react';
import Widget from './../Widget'
import Socket from './../../../Socket.js'

class MediaPlayerWidget extends Component {
  constructor(props) {
    super(props);
    this.state = {playerData: {}, mediaData: {}};
    this.playerUpdate = this.playerUpdate.bind(this);
    this.mediaUpdate = this.mediaUpdate.bind(this);
  }

  componentDidMount() {
    Socket.subscribe("player", this.playerUpdate);
    Socket.subscribe("media", this.mediaUpdate);
  }

  playerUpdate(data){
    this.setState({playerData: data});
  }
  mediaUpdate(data){
    this.setState({mediaData: data});
  }

  render() {
    const playerData = this.state.playerData;
    const mediaData = this.state.mediaData;
    return (
      <Widget>
          {mediaData.type}: {mediaData.title}
          {playerData.playing_for}
      </Widget>
    );
  }
};

export default MediaPlayerWidget;