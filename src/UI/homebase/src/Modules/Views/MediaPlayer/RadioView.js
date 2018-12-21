import React, { Component } from 'react';
import axios from 'axios';

import View from './../View.js';
import SelectInstancePopup from './../../Components/Popups/SelectInstancePopup.js';
import MediaThumbnail from './../../MediaList/MediaThumbnail.js';

class RadioView extends Component {
  constructor(props) {
    super(props);
    this.state = {radios: [], showPopup: false};

    this.selectedRadio = null;
    this.props.changeBack({ to: "/mediaplayer/" });

    this.instanceSelectCancel = this.instanceSelectCancel.bind(this);
    this.instanceSelect = this.instanceSelect.bind(this);
  }

  componentDidMount() {
    axios.get('http://localhost/radio/get_radios').then(data => {
            console.log(data.data);
            for (var i = 0; i < data.data.length; i++){
                import("./../../../Images/radios/radio1.gif").then((r) =>{
                    data.data[i].imgSrc = r;
                }, function(e){
                    console.log("Failed to load radio img: ", e);
                });
            }
            this.setState({radios: data.data});
        }, err =>{
            console.log(err);
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
    this.setState({showPopup: false});
    axios.post('http://localhost/radio/play_radio?instance=' + instance + "&id=" + this.selectedRadio.Id);

  }

  render() {
    const radios = this.state.radios;
    const showPopup = this.state.showPopup;

    return (
      <div className="radio">
        { radios.map((radio, index) => <div key={radio.id} onClick={(e) => this.radioClick(radio, e)}><MediaThumbnail img={radio.imgSrc} title={radio.name}></MediaThumbnail></div>) }
        <SelectInstancePopup show={showPopup} onCancel={this.instanceSelectCancel} onSelect={this.instanceSelect} />
      </div>
    );
  }
};

export default RadioView;