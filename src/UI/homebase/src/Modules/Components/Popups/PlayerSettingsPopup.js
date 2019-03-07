import React, { Component } from 'react';
import axios from 'axios';

import Popup from "./Popup.js"
import Button from "./../Button"

import { InfoGroup, InfoRow } from './../../Components/InfoGroup'
import Slider from './../../Components/Slider';

import seenImage from './../../../Images/watched.svg';
import SvgImage from './../../Components/SvgImage';
import plusImage from './../../../Images/plus.svg';
import minusImage from './../../../Images/minus.svg';

class PlayerSettingsPopup extends Component {
  constructor(props) {
    super(props);
    this.state = {};

    this.close = this.close.bind(this);
    this.increaseSubDelay = this.increaseSubDelay.bind(this);
    this.decreaseSubDelay = this.decreaseSubDelay.bind(this);
  }

  close(){
    this.props.onClose();
  }

  increaseSubDelay(){
    var value = this.props.playerData.sub_delay + 0.2 * 1000 * 1000;
    this.props.onSubDelayChange(value);
  }

  decreaseSubDelay(){
    var value = this.props.playerData.sub_delay - 0.2 * 1000 * 1000;
    this.props.onSubDelayChange(value);
  }

  render() {
    const buttons = (
        <div>
         <Button classId="secondary" text="Ok" onClick={this.close} />
         </div>
    )
    return (
    <Popup title="Player settings"  classId="player-settings-popup" loading={false} buttons={buttons}>
        { (this.props.playerData.sub_tracks.length > 0 || this.props.playerData.audio_tracks.length > 2) &&
            <div className="player-details-track-select">
                { this.props.playerData.sub_tracks.length > 0 &&
                    <div className={"player-details-subtitle-select"}>
                        <InfoGroup title="Subtitles">
                            <div className="player-group-details">
                                { this.props.playerData.sub_tracks.map((o) => (
                                    <div key={o[0]} className="selection-box-option" onClick={() => this.props.onSubTrackChange(o[0])}>
                                        <div className="selection-box-option-radio"><input value={o[0]} type="radio" checked={this.props.playerData.sub_track === o[0]} /></div>
                                        <div className="selection-box-option-title truncate">{o[1]}</div>
                                    </div> )
                                ) }
                                <div className="player-details-delay-slider"><Slider formatMinMax={(e) => { return "";}} format={(e) => {return (e / 1000 / 1000 - 5).toFixed(1);}} min={0} max={10 * 1000 * 1000} value={this.props.playerData.sub_delay + 5 *1000 * 1000} onChange={(v) => this.delayChange(v - 5 * 1000 * 1000)} /></div>
                                <div className="player-details-sub-delay-controls">
                                    <div className="player-details-sub-delay-min" onClick={this.decreaseSubDelay}><SvgImage src={minusImage} /></div>
                                    <div className="player-details-sub-delay-plus" onClick={this.increaseSubDelay}><SvgImage src={plusImage} /></div>
                                </div>
                            </div>
                        </InfoGroup>
                    </div>
                 }
                { this.props.playerData.audio_tracks.length > 1 &&
                    <div className={"player-details-subtitle-select"}>
                        <InfoGroup title="Audio">
                            <div className="player-group-details">
                            { this.props.playerData.audio_tracks.map((o) => (
                                <div  key={o[0]} className="selection-box-option" onClick={() => this.props.onAudioTrackChange(o[0])}>
                                    <div className="selection-box-option-radio"><input value={o[0]} type="radio" checked={this.props.playerData.audio_track === o[0]} /></div>
                                    <div className="selection-box-option-title truncate">{o[1]}</div>
                                </div> )
                            ) }
                            </div>
                        </InfoGroup>
                    </div>
                }
           </div>
        }
    </Popup>
    )
  }
};
export default PlayerSettingsPopup;
