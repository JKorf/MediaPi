import React, { Component } from 'react';
import axios from 'axios';

import View from './../View.js';
import MediaPlayerView from './MediaPlayerView.js';
import SelectInstancePopup from './../../Components/Popups/SelectInstancePopup.js';
import Popup from './../../Components/Popups/Popup.js';
import MediaThumbnail from './../../MediaList/MediaThumbnail.js';

import {radio1, radio2, radio3, radio538, qmusic, veronica, veronicarockradio, top1000, arrowclassicrock, slam, skyradio} from './../../../Images/radios/'

class RadioView extends Component {
  constructor(props) {
    super(props);
    this.viewRef = React.createRef();
    this.state = {radios: []};

    this.selectedRadio = null;
    this.props.changeBack({ to: "/mediaplayer/" });
    this.props.changeTitle("Radio");

    this.imgSrcs = {
        "radio1": radio1,
        "radio2": radio2,
        "3fm": radio3,
        "538": radio538,
        "qmusic": qmusic,
        "skyradio": skyradio,
        "veronica": veronica,
        "veronicarockradio": veronicarockradio,
        "top1000": top1000,
        "arrowclassicrock": arrowclassicrock,
        "slam": slam,
    }

    this.radioClick = this.radioClick.bind(this);
    this.playRadio = this.playRadio.bind(this);
  }

  componentDidMount() {
    axios.get('http://localhost/radio/get_radios').then(data => {
        console.log(data.data);
        this.setState({radios: data.data});
        this.viewRef.current.changeState(1);
    }, err =>{
        console.log(err);
        this.viewRef.current.changeState(1);
    });
  }

  radioClick(radio){
     this.viewRef.current.play(radio);
  }

  playRadio(instance, radio){
    this.viewRef.current.changeState(0);
    axios.post('http://localhost/play/radio?instance=' + instance + "&id=" + radio.id)
    .then(
        () => this.viewRef.current.changeState(1),
        ()=> this.viewRef.current.changeState(1)
    );
  }

  getImgUrl(src)
  {
      return this.imgSrcs[src];
  }

  render() {
    const radios = this.state.radios;

    return (
        <MediaPlayerView ref={this.viewRef} playMedia={this.playRadio}>
          <div className="radio media-overview">
            { radios.map((radio, index) => <a key={radio.id} onClick={(e) => this.radioClick(radio, e)}><MediaThumbnail img={this.getImgUrl(radio.poster)} title={radio.title}></MediaThumbnail></a>) }
          </div>
      </MediaPlayerView>
    );
  }
};

export default RadioView;