import React, { Component } from 'react';
import axios from 'axios';

import MediaPlayerView from './MediaPlayerView.js';
import MediaThumbnail from './../../MediaList/MediaThumbnail.js';
import ViewLoader from './../../Components/ViewLoader/ViewLoader'

import {radio1, radio2, radio3, radio538, qmusic, veronica, veronicarockradio, top1000, arrowclassicrock, slam, skyradio} from './../../../Images/radios/'

class RadioView extends Component {
  constructor(props) {
    super(props);
    this.viewRef = React.createRef();
    this.state = {radios: [], loading: true};

    this.selectedRadio = null;
    this.props.functions.changeBack({ to: "/mediaplayer/" });
    this.props.functions.changeTitle("Radio");
    this.props.functions.changeRightImage(null);

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
    axios.get(window.vars.apiBase + 'radios').then(data => {
        console.log(data.data);
        this.setState({radios: data.data, loading: false});
    }, err =>{
        console.log(err);
        this.setState({loading: false});
    });
  }

  radioClick(radio){
     this.viewRef.current.play(radio);
  }

  playRadio(instance, radio){
    this.setState({loading: true});
    axios.post(window.vars.apiBase + 'play/radio?instance=' + instance + "&id=" + radio.id)
    .then(
        () => this.setState({loading: false}),
        () => this.setState({loading: false})
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
          <ViewLoader loading={this.state.loading}/>
          <div className="radio media-overview">
            { radios.map((radio, index) => <span key={radio.id} onClick={(e) => this.radioClick(radio, e)}><MediaThumbnail img={this.getImgUrl(radio.poster)} title={radio.title}></MediaThumbnail></span>) }
          </div>
      </MediaPlayerView>
    );
  }
};

export default RadioView;