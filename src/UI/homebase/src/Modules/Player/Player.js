import React, { Component } from 'react';

class Player extends Component {
  constructor(props) {
    super(props);
    this.state = {playerData: {}};
    this.socket = null;

     this.socketOpen = this.socketOpen.bind(this);
     this.socketMessage = this.socketMessage.bind(this);
     this.socketClose = this.socketClose.bind(this);
  }

  componentDidMount() {
    this.socket = new WebSocket('ws://localhost/ws');
    this.socket.onopen = this.socketOpen;
    this.socket.onmessage = this.socketMessage;
    this.socket.close = this.socketClose;
    this.socket.onerror = function(){
        console.log("error");
    }
  }

  socketOpen(){
    console.log("Websocket opened");
    this.socket.send(JSON.stringify({ event: "subscribe", topic: "player" }));
  }

  socketMessage(e){
    this.setState({playerData: JSON.parse(e.data).data});
  }

  socketClose(){
     console.log("Websocket closed");
  }

  componentWillUnmount(){
  }

  render() {
    const playerData = this.state.playerData;
    return (
      <div className="player">
        {playerData.playing_for} - {playerData.length}
      </div>
    );
  }
};
export default Player;