import React, { Component } from 'react';

import SelectMediaPopup from './Components/Popups/SelectMediaPopup.js';
import ContinueNextEpisodePopup from './Components/Popups/ContinueNextEpisodePopup.js';
import Socket from './../Socket.js';

class PopupController extends Component {
  constructor(props) {
    super(props);
    this.state = { mediaSelect: {show: false, files: [], id: 0 }, continueNextEpisode:{show: false} };
    this.showSelectMediaFile = this.showSelectMediaFile.bind(this);
    this.showContinueNextEpisode = this.showContinueNextEpisode.bind(this);

    this.test = this.test.bind(this);
    this.selectMediaFile = this.selectMediaFile.bind(this);
    this.cancelMediaSelect = this.cancelMediaSelect.bind(this);

    this.continueNextEpisode = this.continueNextEpisode.bind(this);
    this.cancelNextEpisode = this.cancelNextEpisode.bind(this);
  }

  componentDidMount() {
    Socket.addRequestHandler("SelectMediaFile", this.showSelectMediaFile);
    Socket.addRequestHandler("SelectNextEpisode", this.showContinueNextEpisode);
    Socket.addRequestHandler("Test", this.test);
  }

  componentWillUnmount(){
  }

  test(id, show, instance_id, data)
  {
      Socket.response(id, instance_id, false);
  }

  showSelectMediaFile(id, show, instance_id, files){
    this.setState({mediaSelect: {show: show, files: files[0], id: id, instanceId: instance_id}});
  }

  selectMediaFile(file){
    this.setState({mediaSelect: {show: false}});
    Socket.response(this.state.mediaSelect.id, this.state.mediaSelect.instanceId, file);
  }

  cancelMediaSelect(){
    this.setState({mediaSelect: {show: false}});
    Socket.response(this.state.mediaSelect.id, this.state.mediaSelect.instanceId, null)
  }

  showContinueNextEpisode(id, show, instance_id, title){
    this.setState({continueNextEpisode: {show: show, title: title, id: id, instanceId: instance_id}});
  }

  continueNextEpisode()
  {
    this.setState({continueNextEpisode: {show: false}});
    Socket.response(this.state.continueNextEpisode.id, this.state.continueNextEpisode.instanceId, true)
    console.log("Continue");
  }

  cancelNextEpisode()
  {
      this.setState({continueNextEpisode: {show: false}});
      Socket.response(this.state.continueNextEpisode.id, this.state.continueNextEpisode.instanceId, false)
      console.log("Dont continue");
  }

  render()
  {
    return (
        <div>
        { this.state.mediaSelect.show == true &&
            <SelectMediaPopup files={this.state.mediaSelect.files} onSelect={this.selectMediaFile} onCancel={this.cancelMediaSelect} />
        }

        { this.state.continueNextEpisode.show == true &&
            <ContinueNextEpisodePopup title={this.state.continueNextEpisode.title} onSelect={this.continueNextEpisode} onCancel={this.cancelNextEpisode} />
        }
        </div>
    )
  }
};

export default PopupController;