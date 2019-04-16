import React, { Component } from 'react';
import Popup from "./Popup.js"
import Button from "./../Button"

class ConfirmPopup extends Component {
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
    const buttons = (
        <div>
         <Button classId="secondary" text="Cancel" onClick={this.cancel} />
         <Button classId="secondary" text="Confirm"  onClick={this.confirm} />
         </div>
    )
    return (
    <Popup title={this.props.title} loading={this.props.loading} buttons={buttons}>
        {this.props.text}
    </Popup>
    )
  }
};
export default ConfirmPopup;
