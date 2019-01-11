import React, { Component } from 'react';
import axios from 'axios';

import View from './../View.js';
import MediaPlayerView from './MediaPlayerView.js'
import Socket from './../../../Socket.js';

import Button from './../../Components/Button';
import SelectionBox from './../../Components/SelectionBox';
import SvgImage from './../../Components/SvgImage';
import Slider from './../../Components/Slider';
import SelectInstancePopup from './../../Components/Popups/SelectInstancePopup'
import StopPopup from './../../Components/Popups/StopPopup'
import Popup from './../../Components/Popups/Popup'
import { InfoGroup, InfoRow } from './../../Components/InfoGroup'

import videoFile from './../../../Images/video_file.png';
import stopImage from './../../../Images/stop.svg';
import pauseImage from './../../../Images/pause.svg';
import playImage from './../../../Images/play.svg';
import speakerImage from './../../../Images/speaker.svg';
import plusImage from './../../../Images/plus.svg';
import minusImage from './../../../Images/minus.svg';

class PlayerView extends Component {
  constructor(props) {
    super(props);
    this.props.functions.changeBack({to: "/mediaplayer/players/" });
    this.states = ["loading", "nothing", "confirmStop"];

    this.changedTitle = false;
    this.state = {playerData: { sub_tracks: [], audio_tracks: []}, mediaData: {}, torrentData: {}, stateData: {}, state: this.states[1]};

    this.playerUpdate = this.playerUpdate.bind(this);
    this.mediaUpdate = this.mediaUpdate.bind(this);
    this.torrentUpdate = this.torrentUpdate.bind(this);
    this.stateUpdate = this.stateUpdate.bind(this);
    this.pausePlayClick = this.pausePlayClick.bind(this);
    this.stopClick = this.stopClick.bind(this);
    this.confirmStop = this.confirmStop.bind(this);
    this.seek = this.seek.bind(this);
    this.subChange = this.subChange.bind(this);
    this.audioChange = this.audioChange.bind(this);
    this.volumeChange = this.volumeChange.bind(this);
    this.delayChange = this.delayChange.bind(this);
    this.increaseSubDelay = this.increaseSubDelay.bind(this);
    this.decreaseSubDelay = this.decreaseSubDelay.bind(this);
  }

  componentDidMount() {
    this.stateSub = Socket.subscribe(this.props.match.params.id + ".state", this.stateUpdate);
    this.playerSub = Socket.subscribe(this.props.match.params.id + ".player", this.playerUpdate);
    this.mediaSub = Socket.subscribe(this.props.match.params.id + ".media", this.mediaUpdate);
    this.torrentSub = Socket.subscribe(this.props.match.params.id + ".torrent", this.torrentUpdate);
  }

  componentWillUnmount(){
    Socket.unsubscribe(this.stateSub);
    Socket.unsubscribe(this.playerSub);
    Socket.unsubscribe(this.mediaSub);
    Socket.unsubscribe(this.torrentSub);
  }

  stateUpdate(data){
    if(!this.changedTitle)
    {
        this.changedTitle = true;
        this.props.functions.changeTitle(data.name);
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

  pausePlayClick(e){
    this.setState({state: this.states[0]});
    e.preventDefault();

    axios.post('http://localhost/play/pause_resume_player?instance=' + this.props.match.params.id)
    .then(
        () => this.setState({state: this.states[1]}),
        ()=> this.setState({state: this.states[1]})
    );
    const playerData = this.state.playerData;
    playerData.state = (playerData.state == 3 ? 4: 3);
    this.setState({playerData: playerData});
  }

  stopClick(e){
    this.setState({state: this.states[2]});
    e.preventDefault();
  }

  confirmStop(e){
    this.setState({state: this.states[0]});
    axios.post('http://localhost/play/stop_player?instance=' + this.props.match.params.id)
    .then(
        () => this.setState({state: this.states[1]}),
        ()=> this.setState({state: this.states[1]})
    );
  }

  seek(newValue){
    console.log("Seeking to " + newValue);
    var playerData = this.state.playerData;
    playerData.playing_for = newValue;
    this.setState({state: this.states[0], playerData: playerData});
    axios.post('http://localhost/play/seek?instance=' + this.props.match.params.id + "&position=" + Math.round(newValue))
    .then(
        () => this.setState({state: this.states[1]}),
        ()=> this.setState({state: this.states[1]})
    );
  }

  subChange(value){
    console.log("Change sub: " + value);
    var playerData = this.state.playerData;
    playerData.sub_track = value;
    this.setState({state: this.states[0], playerData: playerData});
    axios.post('http://localhost/play/change_subtitle?instance=' + this.props.match.params.id + "&track=" + value)
    .then(
        () => this.setState({state: this.states[1]}),
        ()=> this.setState({state: this.states[1]})
    );
  }

  audioChange(value){
    console.log("Change audio: " + value);
    var playerData = this.state.playerData;
    playerData.audio_track = value;
    this.setState({state: this.states[0], playerData: playerData});
    axios.post('http://localhost/play/change_audio?instance=' + this.props.match.params.id + "&track=" + value)
    .then(
        () => this.setState({state: this.states[1]}),
        ()=> this.setState({state: this.states[1]})
    );
  }

  volumeChange(value){
    console.log("Change volume: " + value);
    var playerData = this.state.playerData;
    playerData.volume = value;
    this.setState({state: this.states[0], playerData: playerData});
    axios.post('http://localhost/play/change_volume?instance=' + this.props.match.params.id + "&volume=" + Math.round(value))
    .then(
        () => this.setState({state: this.states[1]}),
        ()=> this.setState({state: this.states[1]})
    );
  }

  delayChange(value){
    console.log("Change sub delay: " + value);
    var playerData = this.state.playerData;
    playerData.sub_delay = value;
    this.setState({state: this.states[0], playerData: playerData});
    axios.post('http://localhost/play/change_sub_delay?instance=' + this.props.match.params.id + "&delay=" + Math.round(value))
    .then(
        () => this.setState({state: this.states[1]}),
        ()=> this.setState({state: this.states[1]})
    );
  }

  increaseSubDelay(){
    var value = this.state.playerData.sub_delay + 0.2 * 1000 * 1000;
    this.delayChange(value);
  }

  decreaseSubDelay(){
    var value = this.state.playerData.sub_delay - 0.2 * 1000 * 1000;
    this.delayChange(value);
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

  writeTimespan(duration)
  {
     duration = Math.round(duration);
     var milliseconds = parseInt((duration % 1000) / 100),
      seconds = parseInt((duration / 1000) % 60),
      minutes = parseInt((duration / (1000 * 60)) % 60),
      hours = parseInt((duration / (1000 * 60 * 60)) % 24);

      hours = (hours < 10) ? "0" + hours : hours;
      minutes = (minutes < 10) ? "0" + minutes : minutes;
      seconds = (seconds < 10) ? "0" + seconds : seconds;

      if (hours > 0)
        return hours + ":" + minutes + ":" + seconds;
      return minutes + ":" + seconds;
  }

  capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
  }

  render() {

    let torrentComponent = "";
    if (this.state.torrentData.title)
        torrentComponent = (
            <InfoGroup title="Torrent">
                <InfoRow name="Torrent name" value={this.state.torrentData.title} />
                <InfoRow name="Media name" value={this.state.torrentData.media_file} />
                <InfoRow name="Speed" value={this.writeSpeed(this.state.torrentData.download_speed)} />
                <InfoRow name="Downloaded" value={this.writeSize(this.state.torrentData.downloaded)} />
                <InfoRow name="Left" value={this.writeSize(this.state.torrentData.left)} />
                <InfoRow name="Size" value={this.writeSize(this.state.torrentData.size)} />
                <InfoRow name="Overhead" value={this.writeSpeed(this.state.torrentData.overhead)} />
            </InfoGroup>
        )

    let streamingComponent = "";
    if (this.state.torrentData.title)
        streamingComponent = (
            <InfoGroup title="Streaming">
                <InfoRow name="Stream position" value={this.state.torrentData.stream_position} />
                <InfoRow name="Buffer position" value={this.state.torrentData.buffer_position} />
                <InfoRow name="Buffer ready" value={this.writeSize(this.state.torrentData.buffer_size)} />
                <InfoRow name="Buffer total" value={this.writeSize(this.state.torrentData.buffer_total)} />
                <InfoRow name="Total streamed" value={this.writeSize(this.state.torrentData.total_streamed)} />
            </InfoGroup>
        )

    let playPauseButton = <SvgImage key={this.state.playerData.state} src={pauseImage} />
    if (this.state.playerData.state === 4)
        playPauseButton = <SvgImage key={this.state.playerData.state} src={playImage} />

    let subtitleClass= "both";
    if(this.state.playerData.sub_tracks.length == 0 || this.state.playerData.audio_tracks.length <= 2)
        subtitleClass = "single";

    return (
        <div className="player-details">
            <InfoGroup title="Media">
                { this.state.mediaData.title &&
                    <div>
                        <div className="player-details-top">
                            <div className="player-details-img"><img src={(this.state.mediaData.image ? this.state.mediaData.image: videoFile)} /></div>
                            <div className="player-details-media">
                                <div className="player-details-title">{this.state.mediaData.title}</div>
                                <div className="player-details-type">{this.capitalizeFirstLetter(this.state.mediaData.type)}</div>
                                <div className="player-details-bot">
                                    <div className="player-details-controls">
                                        <div className="player-details-control" onClick={this.pausePlayClick}>
                                            {playPauseButton}
                                        </div>
                                        <div className="player-details-control" onClick={this.stopClick}>
                                             <SvgImage src={stopImage} />
                                        </div>
                                        <div className="player-details-volume">
                                            <Slider format={(e) => {return Math.round(e) + "%";}} iconLeft={speakerImage} min={0} max={100} value={this.state.playerData.volume} onChange={this.volumeChange} />
                                        </div>
                                    </div>
                                    <div className="player-details-slider"><Slider leftValue="value" format={this.writeTimespan} min={0} max={this.state.playerData.length} value={this.state.playerData.playing_for} onChange={this.seek} />
                                    </div>
                                </div>
                            </div>
                        </div>

                        { (this.state.playerData.sub_tracks.length > 0 || this.state.playerData.audio_tracks.length > 2) &&
                            <div className="player-details-track-select">
                                { this.state.playerData.sub_tracks.length > 0 &&
                                    <div className={"player-details-subtitle-select " + subtitleClass}>
                                        <InfoGroup title="Subtitles">
                                            { this.state.playerData.sub_tracks.map((o) => (
                                                <div key={o[0]} className="selection-box-option" onClick={() => this.subChange(o[0])}>
                                                    <div className="selection-box-option-radio"><input value={o[0]} type="radio" checked={this.state.playerData.sub_track == o[0]} /></div>
                                                    <div className="selection-box-option-title truncate">{o[1]}</div>
                                                </div> )
                                            ) }
                                            <div className="player-details-delay-slider"><Slider formatMinMax={(e) => { return "";}} format={(e) => {return (e / 1000 / 1000 - 5).toFixed(1);}} min={0} max={10 * 1000 * 1000} value={this.state.playerData.sub_delay + 5 *1000 * 1000} onChange={(v) => this.delayChange(v - 5 * 1000 * 1000)} /></div>
                                            <div className="player-details-sub-delay-controls">
                                                <div className="player-details-sub-delay-min" onClick={this.decreaseSubDelay}><SvgImage src={minusImage} /></div>
                                                <div className="player-details-sub-delay-plus" onClick={this.increaseSubDelay}><SvgImage src={plusImage} /></div>
                                            </div>
                                        </InfoGroup>
                                    </div>
                                 }
                                { this.state.playerData.audio_tracks.length > 2 &&
                                    <div className={"player-details-subtitle-select " + subtitleClass}>
                                        <InfoGroup title="Audio">
                                            { this.state.playerData.audio_tracks.map((o) => (
                                                <div  key={o[0]} className="selection-box-option" onClick={() => this.audioChange(o[0])}>
                                                    <div className="selection-box-option-radio"><input value={o[0]} type="radio" checked={this.state.playerData.audio_track == o[0]} /></div>
                                                    <div className="selection-box-option-title truncate">{o[1]}</div>
                                                </div> )
                                            ) }
                                        </InfoGroup>
                                    </div>
                                }
                            </div>
                        }
                    </div>
                }
                { !this.state.mediaData.title &&
                    <div>Nothing playing</div>
                }
            </InfoGroup>
             {streamingComponent}

             {torrentComponent}

            <InfoGroup title="System state">
                <InfoRow name="CPU" value={this.state.stateData.cpu + "%"} />
                <InfoRow name="Memory" value={this.state.stateData.memory + "%"} />
                <InfoRow name="Threads" value={this.state.stateData.threads} />
            </InfoGroup>
            { this.state.state == this.states[0] &&
                <Popup loading={true} />
            }
            { this.state.state == this.states[2] &&
                <StopPopup title={this.state.mediaData.title} onConfirm={this.confirmStop} onCancel={()=> this.setState({state: this.states[1]})}/>
            }
        </div>
    );
  }
};

export default PlayerView;