import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";
import ConfirmPopup from "./ConfirmPopup.js"
import Button from "./../Button"

import Socket from "./../../../Socket.js"

class StartMediaPopup extends Component {
  constructor(props) {
    super(props);
    this.state = {mediaData: {}, instance: 0, loading: true};

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

  mediaUpdate(data){
    this.setState({mediaData: data});

    if (!data.title)
        this.confirm(); // Nothing playing, continue
    else
        this.setState({loading: false});
  }

  cancel()
  {
    this.props.onCancel();
    console.log("Cancel");
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
