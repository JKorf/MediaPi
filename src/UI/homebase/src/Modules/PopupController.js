import React, { Component } from 'react';

import SelectMediaPopup from './Components/Popups/SelectMediaPopup.js';
import ContinueNextEpisodePopup from './Components/Popups/ContinueNextEpisodePopup.js';
import Socket from './../Socket.js';

class PopupController extends Component {
  constructor(props) {
    super(props);
    this.state = { mediaSelect: {show: false, files: [], id: 0 }, continueNextEpisode:{show: false}, currentPopup: null, popups: [] };
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

  selectMediaFile(file, start_from){
    this.setState({mediaSelect: {show: false}});
    Socket.response(this.state.mediaSelect.id, this.state.mediaSelect.instanceId, [file.path, start_from]);
  }

  cancelMediaSelect(){
    this.setState({mediaSelect: {show: false}});
    Socket.response(this.state.mediaSelect.id, this.state.mediaSelect.instanceId, [null, 0])
  }

  showContinueNextEpisode(id, show, instance_id, title){
    this.setState({continueNextEpisode: {show: show, title: title, id: id, instanceId: instance_id}});
  }

  continueNextEpisode()
  {
    this.setState({continueNextEpisode: {show: false}});
    Socket.response(this.state.continueNextEpisode.id, this.state.continueNextEpisode.instanceId, [true])
  }

  cancelNextEpisode()
  {
      this.setState({continueNextEpisode: {show: false}});
      Socket.response(this.state.continueNextEpisode.id, this.state.continueNextEpisode.instanceId, [false])
  }

  showPopup(popup)
  {
    if(this.state.currentPopup){
        var list = this.state.popups;
        list.push(popup);
        this.setState({popups:list });
    }
    else
    {
        this.setState({currentPopup: popup});
    }
  }

  closePopup(popup)
  {
    if(this.state.currentPopup === popup)
    {
        if(this.state.popups.length > 0)
        {
            var poplist = this.state.popups;
            var newPopup = poplist.splice(0, 1);
            this.setState({currentPopup: newPopup, popups: poplist});
        }
        else
        {
            this.setState({currentPopup: null});
        }
    }
    else
    {
        var index = this.state.popups.indexOf(popup);
        if(index === -1)
            return;

        var list = this.state.popups;
        list.splice(index, 1);
        this.setState({popups:list});
    }
  }

  render()
  {
    return (
        <div>
        { this.state.mediaSelect.show === true &&
            <SelectMediaPopup files={this.state.mediaSelect.files} onSelect={this.selectMediaFile} onCancel={this.cancelMediaSelect} />
        }

        { this.state.continueNextEpisode.show === true &&
            <ContinueNextEpisodePopup title={this.state.continueNextEpisode.title} onSelect={this.continueNextEpisode} onCancel={this.cancelNextEpisode} />
        }
        {  this.state.currentPopup &&
            this.state.currentPopup
        }
        </div>
    )
  }
};

export default PopupController;