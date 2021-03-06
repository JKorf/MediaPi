import React, { Component } from 'react';
import ConfirmPopup from "./ConfirmPopup.js"

import Socket from "./../../../Socket2.js"

class StartMediaPopup extends Component {
  constructor(props) {
    super(props);
    this.state = {mediaData: {}, instance: 0, loading: true};

    this.confirmed = false;

    this.mediaUpdate = this.mediaUpdate.bind(this);
    this.cancel = this.cancel.bind(this);
    this.confirm = this.confirm.bind(this);
  }

  componentDidMount() {
     this.mediaSub = Socket.subscribe(this.props.instance + ".media", this.mediaUpdate);
  }

  componentWillUnmount() {
    Socket.unsubscribe(this.mediaSub);
  }

  mediaUpdate(subId, data){
    this.setState({mediaData: data});

    if (!data.title && !this.confirmed){
        this.confirmed = true;
        this.confirm(); // Nothing playing, continue
    }
    else
        this.setState({loading: false});
  }

  cancel()
  {
    this.props.onCancel();
  }

  confirm()
  {
    this.props.onConfirm();
  }

  render() {
    const media = this.state.mediaData;
    const title = this.props.title;

    return (
    <ConfirmPopup
        title="Want to play a new media?"
        text={"Do you want to cancel " + media.title +" and play " + title+ "?"}
        loading={this.state.loading}
        onCancel={this.cancel}
        onConfirm={this.confirm}
         />
    )
  }
};
export default StartMediaPopup;
