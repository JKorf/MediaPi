import React, { Component } from 'react';

import SelectInstancePopup from './../../Components/Popups/SelectInstancePopup.js';
import StartMediaPopup from './../../Components/Popups/StartMediaPopup.js';

class MediaPlayerView extends Component {
  constructor(props) {
    super(props);
    this.states = ["nothing", "selectInstance", "confirmPlay"];
    this.state = {state: this.states[0]};

    this.cancel = this.cancel.bind(this);
    this.instanceSelect = this.instanceSelect.bind(this);
    this.playConfirm = this.playConfirm.bind(this);
    this.play = this.play.bind(this);
  }

  changeState(state){
    this.setState({state: this.states[state]});
  }

  play(item)
  {
    console.log(item);
    this.selectedMedia = item;
    this.setState({state: this.states[1]});
  }

  cancel()
  {
    this.setState({state: this.states[0]});
  }

  instanceSelect(instance)
  {
    console.log(instance);
    this.selectedInstance = instance;
    this.setState({state: this.states[2]});
  }

  playConfirm(){
    this.setState({state: this.states[0]});
    this.props.playMedia(this.selectedInstance, this.selectedMedia);
  }

  render() {
    const state = this.state.state;
    return (
      <div className="media-view">
        { this.props.children }
        { state === this.states[1] &&
            <SelectInstancePopup onCancel={this.cancel} onSelect={this.instanceSelect} />
        }
        { state === this.states[2] &&
            <StartMediaPopup onCancel={this.cancel} onConfirm={this.playConfirm} instance={this.selectedInstance} title={this.selectedMedia.title} />
        }
      </div>
    );
  }
};

export default MediaPlayerView;