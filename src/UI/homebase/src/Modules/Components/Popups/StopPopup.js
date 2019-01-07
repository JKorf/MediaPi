import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";
import ConfirmPopup from "./ConfirmPopup.js"
import Button from "./../Button"

import Socket from "./../../../Socket.js"

class StopPopup extends Component {
  constructor(props) {
    super(props);
    this.cancel = this.cancel.bind(this);
    this.confirm = this.confirm.bind(this);
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
    return (
    <ConfirmPopup
        title="Want to stop current media?"
        text={"Do you want to stop " + this.props.title + "?"}
        loading={false}
        onCancel={this.cancel}
        onConfirm={this.confirm}
         />
    )
  }
};
export default StopPopup;
