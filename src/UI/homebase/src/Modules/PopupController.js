import React, { Component } from 'react';

import SelectMediaPopup from './Components/Popups/SelectMediaPopup.js';
import ContinueNextEpisodePopup from './Components/Popups/ContinueNextEpisodePopup.js';
import Socket from './../Socket2.js';

class PopupController extends Component {
  constructor(props) {
    super(props);
    this.state = { mediaSelect: {show: false, files: [], id: 0 }, continueNextEpisode:{show: false}, currentPopup: null, popups: [] };
    this.showSelectMediaFile = this.showSelectMediaFile.bind(this);
    this.showContinueNextEpisode = this.showContinueNextEpisode.bind(this);

    this.timeoutSelectMedia = this.timeoutSelectMedia.bind(this);
    this.timeoutContinue = this.timeoutContinue.bind(this);
    this.selectMediaFile = this.selectMediaFile.bind(this);
    this.cancelMediaSelect = this.cancelMediaSelect.bind(this);

    this.continueNextEpisode = this.continueNextEpisode.bind(this);
  }

  componentDidMount() {
    Socket.addRequestHandler("SelectMediaFile", this.showSelectMediaFile, this.timeoutSelectMedia);
    Socket.addRequestHandler("SelectNextEpisode", this.showContinueNextEpisode, this.timeoutContinue);
    Socket.getCurrentRequests();
  }

  componentWillUnmount(){
  }

  showSelectMediaFile(id, files){
    console.log(files);
    this.setState({mediaSelect: {show: true, files: files, id: id}});
  }

  timeoutSelectMedia(id)
  {
    this.setState({mediaSelect: {show: false}});
  }

  selectMediaFile(file, start_from){
    this.setState({mediaSelect: {show: false}});
    Socket.respond(this.state.mediaSelect.id, file.path, start_from);
  }

  cancelMediaSelect(){
    this.setState({mediaSelect: {show: false}});
    Socket.respond(this.state.mediaSelect.id, null, 0)
  }

  showContinueNextEpisode(id, title){
    console.log(title)
    this.setState({continueNextEpisode: {show: true, title: title, id: id}});
  }

  timeoutContinue(id)
  {
    this.setState({continueNextEpisode: {show: false}});
  }

  continueNextEpisode(continue_next)
  {
    this.setState({continueNextEpisode: {show: false}});
    Socket.respond(this.state.continueNextEpisode.id, continue_next)
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
            <ContinueNextEpisodePopup title={this.state.continueNextEpisode.title} onSelect={() => this.continueNextEpisode(true)} onCancel={() => this.continueNextEpisode(false)} />
        }
        {  this.state.currentPopup &&
            this.state.currentPopup
        }
        </div>
    )
  }
};

export default PopupController;