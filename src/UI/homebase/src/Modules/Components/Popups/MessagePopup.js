import React, { Component } from 'react';
import Popup from "./Popup.js"
import Button from "./../Button"

class MessagePopup extends Component {
  constructor(props) {
    super(props);

    this.close = this.close.bind(this);
  }

  close()
  {
    this.props.onClose();
  }

  render() {
    const buttons = <div><Button classId="secondary" text="Ok" onClick={this.close} /></div>;
    return (
    <Popup title={this.props.title} loading={false} buttons={buttons}>
        {this.props.message}
    </Popup>
    )
  }
};
export default MessagePopup;
