import React, { Component } from 'react';
import Widget from './../Widget'
import Socket from './../../../Socket.js'

class MediaPlayerWidget extends Component {
  constructor(props) {
    super(props);
    this.state = {playerData: {}};
    this.playerUpdate = this.playerUpdate.bind(this);
  }

  componentDidMount() {
    Socket.subscribe("player", this.playerUpdate);
  }

  playerUpdate(data){
    this.setState({playerData: data});
  }

  render() {
    const playerData = this.state.playerData;
    return (
      <Widget>
          {playerData.playing_for}
      </Widget>
    );
  }
};

export default MediaPlayerWidget;