import React, { Component } from 'react';
import axios from 'axios';

import Socket from './../../../Socket.js';

import SvgImage from './../../Components/SvgImage';
import Slider from './../../Components/Slider';
import StopPopup from './../../Components/Popups/StopPopup'
import Popup from './../../Components/Popups/Popup'
import PlayerSettingsPopup from './../../Components/Popups/PlayerSettingsPopup'
import { InfoGroup, InfoRow } from './../../Components/InfoGroup'

import videoFile from './../../../Images/video_file.png';
import stopImage from './../../../Images/stop.svg';
import pauseImage from './../../../Images/pause.svg';
import playImage from './../../../Images/play.svg';
import speakerImage from './../../../Images/speaker.svg';
import plusImage from './../../../Images/plus.svg';
import minusImage from './../../../Images/minus.svg';
import settingsImage from './../../../Images/settings.svg';
import subtitleImage from './../../../Images/subtitle.svg';

class PlayerView extends Component {
  constructor(props) {
    super(props);
    this.props.functions.changeBack({to: "/mediaplayer/players/" });
    this.props.functions.changeRightImage(null);
    this.states = ["loading", "nothing", "confirmStop"];

    this.changedTitle = false;
    this.state = {playerData: { sub_tracks: [], audio_tracks: []}, mediaData: {}, torrentData: {}, stateData: {}, statData: {}, state: this.states[1], showPlayerSettings: false};

    this.playerUpdate = this.playerUpdate.bind(this);
    this.mediaUpdate = this.mediaUpdate.bind(this);
    this.torrentUpdate = this.torrentUpdate.bind(this);
    this.statUpdate = this.statUpdate.bind(this);
    this.stateUpdate = this.stateUpdate.bind(this);
    this.pausePlayClick = this.pausePlayClick.bind(this);
    this.stopClick = this.stopClick.bind(this);
    this.confirmStop = this.confirmStop.bind(this);
    this.seek = this.seek.bind(this);
    this.volumeChange = this.volumeChange.bind(this);
    this.showSettings = this.showSettings.bind(this);

    this.subChange = this.subChange.bind(this);
    this.audioChange = this.audioChange.bind(this);
    this.delayChange = this.delayChange.bind(this);
  }

  componentDidMount() {
    this.stateSub = Socket.subscribe(this.props.match.params.id + ".state", this.stateUpdate);
    this.playerSub = Socket.subscribe(this.props.match.params.id + ".player", this.playerUpdate);
    this.mediaSub = Socket.subscribe(this.props.match.params.id + ".media", this.mediaUpdate);
    this.torrentSub = Socket.subscribe(this.props.match.params.id + ".torrent", this.torrentUpdate);
    this.statSub = Socket.subscribe(this.props.match.params.id + ".stats", this.statUpdate);
  }

  componentWillUnmount(){
    Socket.unsubscribe(this.stateSub);
    Socket.unsubscribe(this.playerSub);
    Socket.unsubscribe(this.mediaSub);
    Socket.unsubscribe(this.torrentSub);
    Socket.unsubscribe(this.statSub);
  }

  stateUpdate(subId, data){
    if(!this.changedTitle)
    {
        this.changedTitle = true;
        this.props.functions.changeTitle(data.name);
    }
    this.setState({stateData: data});
  }
  playerUpdate(subId, data){
    this.setState({playerData: data});
  }
  mediaUpdate(subId, data){
    this.setState({mediaData: data});
  }
  torrentUpdate(subId, data){
    this.setState({torrentData: data});
  }
  statUpdate(subId, data){
    this.setState({statData: data.statistics});
  }

  pausePlayClick(e){
    this.setState({state: this.states[0]});
    e.preventDefault();

    axios.post(window.vars.apiBase + 'play/pause_resume_player?instance=' + this.props.match.params.id)
    .then(
        () => this.setState({state: this.states[1]}),
        ()=> this.setState({state: this.states[1]})
    );
    const playerData = this.state.playerData;
    playerData.state = (playerData.state === 3 ? 4: 3);
    this.setState({playerData: playerData});
  }

  stopClick(e){
    this.setState({state: this.states[2]});
    e.preventDefault();
  }

  confirmStop(e){
    this.setState({state: this.states[0]});
    axios.post(window.vars.apiBase + 'play/stop_player?instance=' + this.props.match.params.id)
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
    axios.post(window.vars.apiBase + 'play/seek?instance=' + this.props.match.params.id + "&position=" + Math.round(newValue))
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
    axios.post(window.vars.apiBase + 'play/change_volume?instance=' + this.props.match.params.id + "&volume=" + Math.round(value))
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
    axios.post(window.vars.apiBase + 'play/change_subtitle?instance=' + this.props.match.params.id + "&track=" + value)
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
    axios.post(window.vars.apiBase + 'play/change_audio?instance=' + this.props.match.params.id + "&track=" + value)
    .then(
        () => this.setState({state: this.states[1]}),
        ()=> this.setState({state: this.states[1]})
    );
  }

  delayChange(value){
    console.log("Change sub delay: " + value);
    var playerData = this.state.playerData;
    playerData.sub_delay = value;
    this.setState({playerData: playerData});
    axios.post(window.vars.apiBase + 'play/change_sub_delay?instance=' + this.props.match.params.id + "&delay=" + Math.round(value));
  }

  writeSize(value){
    if (value < 1000)
        return Math.round(value) + "b";
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
     var seconds = parseInt((duration / 1000) % 60),
      minutes = parseInt((duration / (1000 * 60)) % 60),
      hours = parseInt((duration / (1000 * 60 * 60)) % 24);

      hours = (hours < 10) ? "0" + hours : hours;
      minutes = (minutes < 10) ? "0" + minutes : minutes;
      seconds = (seconds < 10) ? "0" + seconds : seconds;

      if (hours > 0)
        return hours + ":" + minutes + ":" + seconds;
      return minutes + ":" + seconds;
  }

  writeNumber(value){
    if (isNaN(value))
        return 0;

    var f = Math.round(parseFloat(value));
    if(f > 1000)
        f = (Math.round(f / 100) / 10) + "k";
    return f;
  }

  capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
  }

  showSettings(){
    this.setState({showPlayerSettings: true});
  }

  render() {

    let torrentComponent = "";
    if (this.state.torrentData.title)
    {
        var max_dl = " (max " + this.writeSpeed(this.state.torrentData.max_download_speed) + ")";
        if (this.state.torrentData.max_download_speed === 0)
            max_dl = "";
        torrentComponent = (
                <div className="player-group-details">
                    <InfoRow name="Buffer ready" value={this.writeSize(this.state.torrentData.buffer_size)} />
                    <InfoRow name="Total streamed" value={this.writeSize(this.state.torrentData.total_streamed)} />
                    <InfoRow name="Download speed" value={this.writeSpeed(this.state.torrentData.download_speed) + max_dl} />
                    <InfoRow name="Left" value={this.writeSize(this.state.torrentData.left) + " / " + this.writeSize(this.state.torrentData.size)} />
                    <InfoRow name="Peers available" value={this.state.torrentData.potential} />
                    <InfoRow name="Peers connected" value={this.state.torrentData.connected} />
                </div>
        )
    }

    let playPauseButton = <SvgImage key={this.state.playerData.state} src={pauseImage} />
    if (this.state.playerData.state === 4)
        playPauseButton = <SvgImage key={this.state.playerData.state} src={playImage} />

    let subtitleClass= "both";
    if(this.state.playerData.sub_tracks.length === 0 || this.state.playerData.audio_tracks.length <= 2)
        subtitleClass = "single";

    return (
        <div className="player-details">
            { this.state.showPlayerSettings &&
                <PlayerSettingsPopup onClose={() => this.setState({showPlayerSettings: false})} playerData={this.state.playerData} onSubTrackChange={this.subChange} onSubDelayChange={this.delayChange} onAudioTrackChange={this.audioChange}/>
            }
            <InfoGroup title="Media">
                <div className="player-group-details">
                    { this.state.mediaData.title &&
                        <div>
                            <div className="player-details-settings">
                                <div className="player-details-settings-icon" onClick={this.showSettings} ><SvgImage src={settingsImage} /></div>
                            </div>
                            <div className="player-details-top">
                                <div className="player-details-img"><img alt="Media poster" src={(this.state.mediaData.image ? this.state.mediaData.image: videoFile)} /></div>
                                <div className="player-details-media">
                                    <div className="player-details-title truncate">{this.state.mediaData.title}</div>
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
                        </div>
                    }
                    { !this.state.mediaData.title &&
                        <div>Nothing playing</div>
                    }
                </div>

                 {torrentComponent}
            </InfoGroup>

             <InfoGroup title="System statistics">
                <div className="player-group-details">
                 <InfoRow name="Max download speed" value={this.writeSpeed(this.state.statData["max_download_speed"])}></InfoRow>
                 <InfoRow name="Total downloaded" value={this.writeSize(this.state.statData["total_downloaded"])}></InfoRow>

                 <InfoRow name="Peers connected" value={this.writeNumber(this.state.statData["peers_connect_success"]) + " / " + this.writeNumber(this.state.statData["peers_connect_failed"])}></InfoRow>
                 <InfoRow name="DHT peers" value={this.writeNumber(this.state.statData["peers_source_dht"])}></InfoRow>
                 <InfoRow name="Exchange peers" value={this.writeNumber(this.state.statData["peers_source_exchange"])}></InfoRow>
                 <InfoRow name="UDP tracker peers" value={this.writeNumber(this.state.statData["peers_source_udp_tracker"])}></InfoRow>
                 <InfoRow name="Subtitles downloaded" value={this.writeNumber(this.state.statData["subs_downloaded"])}></InfoRow>
                </div>
             </InfoGroup>

            <InfoGroup title="System state">
                <div className="player-group-details">
                    <InfoRow name="CPU" value={this.state.stateData.cpu + "%"} />
                    <InfoRow name="Memory" value={this.state.stateData.memory + "%"} />
                    <InfoRow name="Temperature" value={this.state.stateData.temperature} />
                    <InfoRow name="Threads" value={this.state.stateData.threads} />
                </div>
            </InfoGroup>
            { this.state.state === this.states[0] &&
                <Popup loading={true} />
            }
            { this.state.state === this.states[2] &&
                <StopPopup title={this.state.mediaData.title} onConfirm={this.confirmStop} onCancel={()=> this.setState({state: this.states[1]})}/>
            }
        </div>
    );
  }
};

export default PlayerView;