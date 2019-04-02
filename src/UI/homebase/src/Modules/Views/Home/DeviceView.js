import React, { Component } from 'react';
import axios from 'axios';

import Socket from './../../../Socket2.js';

import SvgImage from './../../Components/SvgImage';
import Button from './../../Components/Button';
import Slider from './../../Components/Slider';
import StopPopup from './../../Components/Popups/StopPopup'
import Popup from './../../Components/Popups/Popup'
import { InfoGroup, InfoRow } from './../../Components/InfoGroup'
import { SwitchBox, SwitchBoxItem } from './../../Components/SwitchBox'
import ViewLoader from './../../Components/ViewLoader';

import videoFile from './../../../Images/video_file.png';
import stopImage from './../../../Images/stop.svg';
import pauseImage from './../../../Images/pause.svg';
import playImage from './../../../Images/play.svg';
import speakerImage from './../../../Images/speaker.svg';
import plusImage from './../../../Images/plus.svg';
import minusImage from './../../../Images/minus.svg';
import cpuImage from './../../../Images/cpu.svg';
import memoryImage from './../../../Images/memory.svg';
import tempImage from './../../../Images/thermometer.svg';

class DeviceView extends Component {
  constructor(props) {
    super(props);
    this.props.functions.changeBack({to: "/home/devices/" });
    this.props.functions.changeRightImage(null);
    this.states = ["loading", "nothing", "confirmStop"];

    this.changedTitle = false;
    this.state = {
        playerData: { sub_tracks: [], audio_tracks: []},
        mediaData: {},
        torrentData: {},
        stateData: {},
        statData: {},
        state: this.states[1],
        currentView: "Media",
        logFiles: [],
        updateState: "Idle",
        currentVersion: "",
        loading: false};

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

    this.subChange = this.subChange.bind(this);
    this.audioChange = this.audioChange.bind(this);
    this.delayChange = this.delayChange.bind(this);

    this.getLogFiles = this.getLogFiles.bind(this);
    this.updateUpdate = this.updateUpdate.bind(this);
  }

  componentDidMount() {
    this.stateSub = Socket.subscribe(this.props.match.params.id + ".state", this.stateUpdate);
    this.playerSub = Socket.subscribe(this.props.match.params.id + ".player", this.playerUpdate);
    this.mediaSub = Socket.subscribe(this.props.match.params.id + ".media", this.mediaUpdate);
    this.torrentSub = Socket.subscribe(this.props.match.params.id + ".torrent", this.torrentUpdate);
    this.statSub = Socket.subscribe(this.props.match.params.id + ".stats", this.statUpdate);
    this.updateSub = Socket.subscribe(this.props.match.params.id + ".update", this.updateUpdate);

    this.getLogFiles();
  }

  componentWillUnmount(){
    Socket.unsubscribe(this.stateSub);
    Socket.unsubscribe(this.playerSub);
    Socket.unsubscribe(this.mediaSub);
    Socket.unsubscribe(this.torrentSub);
    Socket.unsubscribe(this.statSub);
    Socket.unsubscribe(this.updateSub);
  }

  debugLogging(){
    axios.post(window.vars.apiBase + 'util/log')
  }

  getLogFiles(){
    axios.get(window.vars.apiBase + 'util/logs').then((data) => {
        this.setState({logFiles: data.data});
    });
  }

  openLog(file)
  {
    this.setState({loading: true});
    axios.get(window.vars.apiBase + 'util/log?file=' + encodeURIComponent(file)).then((data) => {
        console.log(data);
        var html = data.data.replace(/\r\n/g, '<br />');
        var newWindow = window.open();
        newWindow.document.write("<html><head><title>" + file + "</title></head><body>" + html + "</body></html>");
        newWindow.document.close();
        this.setState({loading: false});
    });
  }

  updateUpdate(id, data)
  {
    this.setState({updateState: data.state, currentVersion: data.current_version, lastUpdate: data.last_update});
    if (data.completed)
    {
        if (data.error)
            alert("Update failed: " + data.error);
    }
  }

  checkUpdates()
  {
    this.setState({loading: true});
    axios.get(window.vars.apiBase + 'util/update?instance=' + this.props.match.params.id).then((data) => {
        this.setState({loading: false});
        if(data.data.available)
        {
            if(window.confirm("New update available, download now?")){
                axios.post(window.vars.apiBase + 'util/update?instance=' + this.props.match.params.id);
            }
        }
        else{
            window.alert("Already up to date")
        }
    });
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

    axios.post(window.vars.apiBase + 'player/pause_resume?instance=' + this.props.match.params.id)
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
    axios.post(window.vars.apiBase + 'player/stop?instance=' + this.props.match.params.id)
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
    axios.post(window.vars.apiBase + 'player/seek?instance=' + this.props.match.params.id + "&position=" + Math.round(newValue))
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
    axios.post(window.vars.apiBase + 'player/volume?instance=' + this.props.match.params.id + "&volume=" + Math.round(value))
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
    axios.post(window.vars.apiBase + 'player/subtitle?instance=' + this.props.match.params.id + "&track=" + value)
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
    axios.post(window.vars.apiBase + 'player/audio?instance=' + this.props.match.params.id + "&track=" + value)
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
    axios.post(window.vars.apiBase + 'player/sub_delay?instance=' + this.props.match.params.id + "&delay=" + Math.round(value));
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

  increaseSubDelay(){
    var value = this.state.playerData.sub_delay + 0.2 * 1000 * 1000;
    this.delayChange(value);
  }

  decreaseSubDelay(){
    var value = this.state.playerData.sub_delay - 0.2 * 1000 * 1000;
    this.delayChange(value);
  }


  render() {

    let torrentComponent = "";
    if (this.state.torrentData.title)
    {
        var download_state = "";
        if (this.state.torrentData.state === 3 && this.state.torrentData.max_download_speed !== 0)
            download_state = " (max " + this.writeSpeed(this.state.torrentData.max_download_speed) + ")";

        if (this.state.torrentData.state === 2) download_state = " (metadata)";
        if (this.state.torrentData.state === 4) download_state = " (paused)";
        if (this.state.torrentData.state === 5) download_state = " (done)";
        if (this.state.torrentData.state === 6) download_state = " (waiting)";

        torrentComponent = (
                <div className="player-group-details">
                    <InfoRow name="Buffer ready" value={this.writeSize(this.state.torrentData.buffer_size)} />
                    <InfoRow name="Total streamed" value={this.writeSize(this.state.torrentData.total_streamed)} />
                    <InfoRow name="Download speed" value={this.writeSpeed(this.state.torrentData.download_speed) + download_state} />
                    <InfoRow name="Left" value={this.writeSize(this.state.torrentData.left) + " / " + this.writeSize(this.state.torrentData.size)} />
                    <InfoRow name="Peers available" value={this.state.torrentData.potential} />
                    <InfoRow name="Peers connected" value={this.state.torrentData.connected} />
                </div>
        )
    }

    let playPauseButton = <SvgImage key={this.state.playerData.state} src={pauseImage} />
    if (this.state.playerData.state === 4)
        playPauseButton = <SvgImage key={this.state.playerData.state} src={playImage} />

    return (
        <div className="player-details">
            <ViewLoader loading={this.state.loading || this.state.updateState !== "Idle"} text={(this.state.updateState !== "Idle" ? this.state.updateState: null)}/>

            <SwitchBox>
                <SwitchBoxItem selected={this.state.currentView === "Media"} text="Media" onClick={() => this.setState({currentView: "Media"})} />
                <SwitchBoxItem selected={this.state.currentView === "Statistics"} text="Statistics" onClick={() => this.setState({currentView: "Statistics"})} />
                <SwitchBoxItem selected={this.state.currentView === "Config"} text="Config" onClick={() => this.setState({currentView: "Config"})} />
            </SwitchBox>

            { this.state.currentView === "Media" &&

                <div className="player-group-details">
                    { this.state.mediaData.title &&
                        <div>
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
                                        <div className="player-details-slider">
                                            <Slider leftValue="value" rightValue="left" format={this.writeTimespan} min={0} max={this.state.playerData.length} value={this.state.playerData.playing_for} onChange={this.seek} />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    }
                    {torrentComponent}
                    { (this.state.playerData.sub_tracks.length > 0 || this.state.playerData.audio_tracks.length > 2) &&
                        <div className="player-details-track-select">
                            { this.state.playerData.sub_tracks.length > 0 &&
                                <div className={"player-details-subtitle-select"}>
                                    <InfoGroup title="Subtitles">
                                        <div className="player-group-details">
                                            { this.state.playerData.sub_tracks.map((o) => (
                                                <div key={o[0]} className="selection-box-option" onClick={() => this.state.onSubTrackChange(o[0])}>
                                                    <div className="selection-box-option-radio"><input value={o[0]} type="radio" checked={this.state.playerData.sub_track === o[0]} /></div>
                                                    <div className="selection-box-option-title truncate">{o[1]}</div>
                                                </div> )
                                            ) }
                                            <div className="player-details-delay-slider"><Slider formatMinMax={(e) => { return "";}} format={(e) => {return (e / 1000 / 1000 - 5).toFixed(1);}} min={0} max={10 * 1000 * 1000} value={this.state.playerData.sub_delay + 5 *1000 * 1000} onChange={(v) => this.delayChange(v - 5 * 1000 * 1000)} /></div>
                                            <div className="player-details-sub-delay-controls">
                                                <div className="player-details-sub-delay-min" onClick={this.decreaseSubDelay}><SvgImage src={minusImage} /></div>
                                                <div className="player-details-sub-delay-plus" onClick={this.increaseSubDelay}><SvgImage src={plusImage} /></div>
                                            </div>
                                        </div>
                                    </InfoGroup>
                                </div>
                             }
                            { this.state.playerData.audio_tracks.length > 2 &&
                                <div className={"player-details-subtitle-select"}>
                                    <InfoGroup title="Audio">
                                        <div className="player-group-details">
                                        { this.state.playerData.audio_tracks.map((o) => (
                                            <div  key={o[0]} className="selection-box-option" onClick={() => this.state.onAudioTrackChange(o[0])}>
                                                <div className="selection-box-option-radio"><input value={o[0]} type="radio" checked={this.state.playerData.audio_track === o[0]} /></div>
                                                <div className="selection-box-option-title truncate">{o[1]}</div>
                                            </div> )
                                        ) }
                                        </div>
                                    </InfoGroup>
                                </div>
                            }
                       </div>
                    }

                    { !this.state.mediaData.title &&
                        <div>Nothing playing</div>
                    }
                </div>
            }

            { this.state.currentView === "Statistics" &&
                <div className="player-group-details">
                 <InfoRow name="Max download speed" value={this.writeSpeed(this.state.statData["max_download_speed"])}></InfoRow>
                 <InfoRow name="Total downloaded" value={this.writeSize(this.state.statData["total_downloaded"])}></InfoRow>

                 <InfoRow name="Peers connected" value={this.writeNumber(this.state.statData["peers_connect_success"]) + " / " + this.writeNumber(this.state.statData["peers_connect_failed"])}></InfoRow>
                 <InfoRow name="DHT peers" value={this.writeNumber(this.state.statData["peers_source_dht"])}></InfoRow>
                 <InfoRow name="Exchange peers" value={this.writeNumber(this.state.statData["peers_source_exchange"])}></InfoRow>
                 <InfoRow name="UDP tracker peers" value={this.writeNumber(this.state.statData["peers_source_udp_tracker"])}></InfoRow>
                 <InfoRow name="Subtitles downloaded" value={this.writeNumber(this.state.statData["subs_downloaded"])}></InfoRow>
                </div>
             }

             { this.state.currentView === "Config" &&
                <div className="player-group-details">
                    <div className="device-config-subtitle">version</div>
                    <div className="device-config-item">
                         <InfoRow name="Current version" value={this.state.currentVersion}></InfoRow>
                         <InfoRow name="Installed at" value={new Intl.DateTimeFormat('en-GB', { year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(1970, 0, 0).setTime(this.state.lastUpdate))}></InfoRow>

                        <div className="device-config-button"><Button text="Check for updates" onClick={() => this.checkUpdates()}/></div>
                    </div>

                    <div className="device-config-subtitle">logs</div>
                    <div className="device-config-item">
                        <div className="device-log-files">
                            { this.state.logFiles.map(file =>
                            <div key={file[1]} className="settings-log" onClick={() => this.openLog(file[1])}>
                                <div className="settings-log-name">{file[0]}</div>
                                <div className="settings-log-size">{file[2]}</div>
                            </div>) }
                        </div>

                        <div className="device-config-button"><Button text="Debug logging" classId="secondary" onClick={() => this.debugLogging()}/></div>
                    </div>
                </div>
             }

            <div className="system-state">
                <div className="system-state-item">
                    <div className="system-state-item-text">{this.state.stateData.cpu + "%"}</div>
                    <div className="system-state-item-icon"><SvgImage src={cpuImage} /></div>
                </div>
                 <div className="system-state-item">
                    <div className="system-state-item-text">{this.state.stateData.memory + "%"}</div>
                    <div className="system-state-item-icon"><SvgImage src={memoryImage} /></div>
                </div>
                 <div className="system-state-item">
                    <div className="system-state-item-text">{this.state.stateData.temperature}</div>
                    <div className="system-state-item-icon"><SvgImage src={tempImage} /></div>
                </div>
            </div>

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

export default DeviceView;