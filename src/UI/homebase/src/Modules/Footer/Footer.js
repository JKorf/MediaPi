import React, { Component } from 'react';
import { Link } from "react-router-dom";
import axios from 'axios';

import FooterLink from "./FooterLink.js";
import Socket from './../../Socket.js';

import SvgImage from './../Components/SvgImage';
import MediaProgress from './../Components/MediaProgress';
import StopPopup from './../Components/Popups/StopPopup.js';

import playImage from './../../Images/play.svg';
import pauseImage from './../../Images/pause.svg';
import stopImage from './../../Images/stop.svg';

import homeImage from "./../../Images/home.svg";
import entertainmentImage from "./../../Images/entertainment.svg";
import lightImage from "./../../Images/bulb.svg";
import settingsImage from "./../../Images/settings.svg";

class Footer extends Component
{
    constructor(props) {
        super(props);
        this.state = {slaveData: []};

        this.slaveUpdate = this.slaveUpdate.bind(this);
        this.mediaUpdate = this.mediaUpdate.bind(this);
        this.playerUpdate = this.playerUpdate.bind(this);

         this.pausePlayClick = this.pausePlayClick.bind(this);
        this.confirmStop = this.confirmStop.bind(this);
        this.cancelStop = this.cancelStop.bind(this);
        this.stopClick = this.stopClick.bind(this);
    }

    componentDidMount() {
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
                sd.mediaSubscription = Socket.subscribe(sd.id + ".media", this.mediaUpdate);
                sd.playerSubscription = Socket.subscribe(sd.id + ".player", this.playerUpdate);

                this.setState(state => {
                  const slaveData = state.slaveData.concat(sd);
                  return {
                    slaveData
                  };
                });
            }
        }
    }

    mediaUpdate(subId, data){
        console.log(subId + ": ", data);
        this.setState(state => {
          const slaveData = state.slaveData.map(s => {
            if(s.mediaSubscription === subId)
                s.mediaData = data;
            return s;
          });

          return {
            slaveData,
          };
        });
    }

    playerUpdate(subId, data){
        this.setState(state => {
          const slaveData = state.slaveData.map(s => {
            if(s.playerSubscription === subId)
                s.playerData = data;
            return s;
          });

          return {
            slaveData,
          };
        });
    }

    pausePlayClick(instance, e){
        axios.post('http://localhost/play/pause_resume_player?instance=' + instance.id);
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
        axios.post('http://localhost/play/stop_player?instance=' + instance.id );
      }

    render () {

      var playing = this.state.slaveData.filter(x => x.mediaData && x.mediaData.title && x.playerData);
      var style = {
        height: (playing.length * 66) + "px"
      };
      return (
      <div className="footer">
        <div className="footer-players" style={style}>
            { playing.map(x => {
                    let playPauseButton = <SvgImage key={x.playerData.state} src={pauseImage} />
                    if (x.playerData.state === 4)
                        playPauseButton = <SvgImage key={x.playerData.state} src={playImage} />

                    let percentagePlaying = x.playerData.playing_for / x.playerData.length * 100;
                    if (x.playerData.length === 0 && x.playerData.playing_for != 0)
                        percentagePlaying = 100;

                    return (
                    <div key={x.id} className={"mediaplayer-widget " + (x.mediaData.title ? "": "not-playing")} >
                        <Link to={"/mediaplayer/player/" + x.id} >
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
                                    <MediaProgress percentage={percentagePlaying} ></MediaProgress>
                                </div>
                                </div>
                        </Link>
                    </div>);
            } ) }
        </div>
        <div className="footer-links">
            <FooterLink to="/" exact={true} img={homeImage} />
            <FooterLink to="/mediaplayer" img={entertainmentImage} />
            <FooterLink to="/light" img={lightImage} />
            <FooterLink to="/settings" img={settingsImage} />
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