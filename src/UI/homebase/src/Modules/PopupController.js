import React, { Component } from 'react';

import SelectMediaPopup from './Components/Popups/SelectMediaPopup.js';
import Socket from './../Socket.js';

class PopupController extends Component {
  constructor(props) {
    super(props);
    this.state = { mediaSelect: {show: false, files: [], id: 0 } };
    this.showSelectMediaFile = this.showSelectMediaFile.bind(this);
    this.test = this.test.bind(this);
    this.selectMediaFile = this.selectMediaFile.bind(this);
    this.cancelMediaSelect = this.cancelMediaSelect.bind(this);
  }

  componentDidMount() {
    Socket.addRequestHandler("SelectMediaFile", this.showSelectMediaFile);
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
    Socket.response(this.state.mediaSelect.id, null)
  }

  render()
  {
    var showMedia = this.state.mediaSelect.show;
    var files = this.state.mediaSelect.files;
    return (
        <div>
        { showMedia == true &&
            <SelectMediaPopup files={files} onSelect={this.selectMediaFile} onCancel={this.cancelMediaSelect} />
        }
        </div>
    )
  }
};

export default PopupController;