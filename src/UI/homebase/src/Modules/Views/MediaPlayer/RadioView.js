import React, { Component } from 'react';
import axios from 'axios';

import View from './../View.js';
import SelectInstancePopup from './../../Components/Popups/SelectInstancePopup.js';
import Popup from './../../Components/Popups/Popup.js';
import MediaThumbnail from './../../MediaList/MediaThumbnail.js';

import {radio1, radio2, radio3, radio538, qmusic, veronica, veronicarockradio, top1000, arrowclassicrock, slam, skyradio} from './../../../Images/radios/'

class RadioView extends Component {
  constructor(props) {
    super(props);
    this.state = {radios: [], showPopup: false, loading: true};

    this.selectedRadio = null;
    this.props.changeBack({ to: "/mediaplayer/" });

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

    this.instanceSelectCancel = this.instanceSelectCancel.bind(this);
    this.instanceSelect = this.instanceSelect.bind(this);
  }

  componentDidMount() {
    axios.get('http://localhost/radio/get_radios').then(data => {
        console.log(data.data);
        this.setState({radios: data.data, loading: false});
    }, err =>{
        console.log(err);
        this.setState({loading: false});
    });
  }

  radioClick(radio){
    this.selectedRadio = radio;
    this.setState({showPopup: true});
  }

  instanceSelectCancel()
  {
    this.setState({showPopup: false});
  }

  instanceSelect(instance)
  {
    this.setState({showPopup: false, loading: true});
    axios.post('http://localhost/play/radio?instance=' + instance + "&id=" + this.selectedRadio.id)
    .then(
        () => this.setState({loading: false}),
        ()=> this.setState({loading: false})
    );
  }

  getImgUrl(src)
  {
      return this.imgSrcs[src];
  }

  render() {
    const radios = this.state.radios;
    const showPopup = this.state.showPopup;
    const loading = this.state.loading;

    return (
      <div className="radio media-overview">
        { radios.map((radio, index) => <a key={radio.id} onClick={(e) => this.radioClick(radio, e)}><MediaThumbnail img={this.getImgUrl(radio.poster)} title={radio.title}></MediaThumbnail></a>) }
        { showPopup &&
            <SelectInstancePopup onCancel={this.instanceSelectCancel} onSelect={this.instanceSelect} />
        }
        { loading &&
            <Popup loading={loading} />
        }
      </div>
    );
  }
};

export default RadioView;