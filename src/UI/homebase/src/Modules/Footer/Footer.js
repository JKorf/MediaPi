/*eslint no-loop-func: "off"*/

import React, { Component } from 'react';
import { Link } from "react-router-dom";
import axios from 'axios';

import FooterLink from "./FooterLink.js";
import Socket from './../../Socket2.js';

import SvgImage from './../Components/SvgImage';
import MediaProgress from './../Components/MediaProgress';
import StopPopup from './../Components/Popups/StopPopup.js';

import playImage from './../../Images/play.svg';
import pauseImage from './../../Images/pause.svg';
import stopImage from './../../Images/stop.svg';

import dashboardImage from "./../../Images/dashboard.svg";
import homeImage from "./../../Images/home.svg";
import entertainmentImage from "./../../Images/entertainment.svg";
import settingsImage from "./../../Images/settings.svg";

import testVideo from "./../../Images/test.mp4";
import videoFile from './../../Images/video_file.png';

class Footer extends Component
{
    constructor(props) {
        super(props);
        this.state = {slaveData: []};

        this.initialMediaDone = false;
        this.currentMediaState = 0;

        this.slaveUpdate = this.slaveUpdate.bind(this);
        this.mediaUpdate = this.mediaUpdate.bind(this);
        this.playerUpdate = this.playerUpdate.bind(this);

        this.pausePlayClick = this.pausePlayClick.bind(this);
        this.confirmStop = this.confirmStop.bind(this);
        this.cancelStop = this.cancelStop.bind(this);
        this.stopClick = this.stopClick.bind(this);
    }

    componentDidMount() {
        this.initializeMediaSession();
        this.slaveSub = Socket.subscribe("slaves", this.slaveUpdate);
    }

    componentWillUnmount(){
        Socket.unsubscribe(this.slaveSub);
        for (var i = 0; i < this.state.slaveData.length; i++){
            Socket.unsubscribe(this.state.slaveData[i].mediaSubscription);
            Socket.unsubscribe(this.state.slaveData[i].playerSubscription);
        }
    }

    slaveUpdate(subId, data){
        for (var i = 0; i < data.length; i++){
            if(!this.state.slaveData.some(x => x.id === data[i].id))
            {
                // New slave
                var sd = new SlaveData(data[i]);
                this.setState(state => {
                  const slaveData = state.slaveData.concat(sd);
                  return {
                    slaveData
                  };
                });

                sd.mediaSubscription = Socket.subscribe(sd.id + ".media", this.mediaUpdate);
                sd.playerSubscription = Socket.subscribe(sd.id + ".player", this.playerUpdate);
            }
        }
    }

    mediaUpdate(subId, data){
        this.updateMediaSessionMetadata(data);
        setTimeout(() => {
            this.setState(state => {
              const slaveData = state.slaveData.map(s => {
                if(s.mediaSubscription === subId){
                    s.mediaData = data;
                }
                return s;
              });

              return {
                slaveData,
              };
            });
        }, 10);
    }

    playerUpdate(subId, data){
        this.updateMediaSessionState(data);
        setTimeout(() => {
            this.setState(state => {
              const slaveData = state.slaveData.map(s => {
                if(s.playerSubscription === subId){
                    s.playerData = data;
                }
                return s;
              });

              return {
                slaveData,
              };
            });
        }, 10);
    }

    updateMediaFromClick(){
        if(this.initialMediaDone)
            return;

        document.getElementById("video-w").load();
        this.initialMediaDone = true;
    }

    initializeMediaSession(){
        if ('mediaSession' in navigator) {
            navigator.mediaSession.setActionHandler('play', () => { this.pausePlayClick(this.state.slaveData[0]); });
            navigator.mediaSession.setActionHandler('pause', () => { this.pausePlayClick(this.state.slaveData[0]); });
        }
    }

    updateMediaSessionState(playerData){
        var paused = playerData.state === 4;
        var playing = playerData.state === 3;
        var videoPlayer = document.getElementById("video-w");
        document.getElementById("video-w").volume = 0;

        if(playing){
            if(this.currentMediaState == 2)
                return;

            this.currentMediaState = 2;
            videoPlayer.src = testVideo;
            videoPlayer.play();
            navigator.mediaSession.playbackState = "playing";

        }else if(paused){
            if(this.currentMediaState == 1)
                return;

            this.currentMediaState = 1;
            navigator.mediaSession.playbackState = "paused";
        }
        else{
            if(this.currentMediaState == 0)
                return;

            this.currentMediaState = 0;
            videoPlayer.pause();
            videoPlayer.removeAttribute('src');
            videoPlayer.load();
        }
    }

    updateMediaSessionMetadata(mediaData)
    {
        if ('mediaSession' in navigator) {
            var image = mediaData.image ? mediaData.image: videoFile;

            navigator.mediaSession.metadata = new window.MediaMetadata({
                title: mediaData.title,
                artwork: [
                  { src: image, sizes: '512x512', type: 'image/png' }
                ]
              });
        }
    }

    pausePlayClick(instance, e){
        axios.post(window.vars.apiBase + 'player/pause_resume?instance=' + instance.id);
        var data = this.state.slaveData;
        if(data[0].playerData.state === 4)
            data[0].playerData.state = 3;
        else
            data[0].playerData.state = 4;
        this.setState({slaveData: data});
        if(e)
            e.preventDefault();
      }

      stopClick(instance, e){
        this.stopPopup = <StopPopup title={instance.mediaData.title} onCancel={this.cancelStop} onConfirm={() => this.confirmStop(instance)} />;
        this.props.functions.showPopup(this.stopPopup);
        e.preventDefault();
      }

      cancelStop(){
        this.props.functions.closePopup(this.stopPopup);
      }

      confirmStop(instance){
        this.props.functions.closePopup(this.stopPopup);
        axios.post(window.vars.apiBase + 'player/stop?instance=' + instance.id );
      }

    render () {
      var playing = this.state.slaveData.filter(x => x.mediaData && x.mediaData.title && x.playerData);
      var style = {
        height: (playing.length * 66) + "px"
      };
      return (
      <div className="footer" onClick={e => this.updateMediaFromClick()}>
        <div className="mobile-video-wrapper">
            <video id="video-w" loop>
              <source src={testVideo} />
            </video>
        </div>
        <div className="footer-players" style={style}>
            { playing.map(x => {
                    let playPauseButton = <SvgImage key={x.playerData.state} src={pauseImage} />
                    if (x.playerData.state === 4)
                        playPauseButton = <SvgImage key={x.playerData.state} src={playImage} />

                    let percentagePlaying = x.playerData.playing_for / x.playerData.length * 100;
                    if (x.playerData.length === 0 && x.playerData.playing_for !== 0)
                        percentagePlaying = 100;

                    return (
                    <div key={x.id} className={"mediaplayer-widget " + (x.mediaData.title ? "": "not-playing")} >
                        <Link to={"/home/device/" + x.id} >
                            <div className="mediaplayer-name">{x.name}</div>
                            <div className="mediaplayer-playing ">
                                 <div className="mediaplayer-widget-content">
                                    <div className="mediaplayer-widget-info">
                                        <div className="mediaplayer-widget-info-title truncate">{x.mediaData.title}</div>
                                    </div>
                                    <div className="mediaplayer-widget-controls">
                                        <div className="mediaplayer-widget-control" onClick={(e) => this.pausePlayClick(x, e)}>
                                            {playPauseButton}
                                        </div>
                                        <div className="mediaplayer-widget-control" onClick={(e) => this.stopClick(x, e)}>
                                             <SvgImage src={stopImage} />
                                        </div>
                                    </div>
                                    <div className="media-player-widget-progress">
                                        <MediaProgress percentage={percentagePlaying} ></MediaProgress>
                                    </div>
                                </div>
                                </div>
                        </Link>
                    </div>);
            } ) }
        </div>
        <div className="footer-links">
            <FooterLink to="/" exact={true} img={dashboardImage} />
            <FooterLink to="/mediaplayer" img={entertainmentImage} />
            <FooterLink to="/home" img={homeImage} />
            <FooterLink to="/configuration" img={settingsImage} />
        </div>
      </div>
    )};
}

class SlaveData
{
    constructor(data){
        this.id = data.id;
        this.name = data.name;
        this.mediaSubscription = null;
        this.playerSubscription = null;
        this.mediaData = null;
        this.playerData = null;
    }
}

export default Footer;