import React, { Component } from 'react';
import ConfirmPopup from "./ConfirmPopup.js"

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
    console.log("Confirm stop click");
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
