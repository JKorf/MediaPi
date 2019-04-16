import React, { Component } from 'react';
import Popup from "./Popup.js"
import Button from "./../Button"

class ContinueNextEpisodePopup extends Component {
  constructor(props) {
    super(props);
    this.state = {};
    this.cancel = this.cancel.bind(this);
    this.select = this.select.bind(this);
  }

  cancel()
  {
    this.props.onCancel();
  }

  select()
  {
    this.props.onSelect();
  }

  render() {
    const buttons = (
        <div>
         <Button classId="secondary" text="Cancel" onClick={this.cancel} />
         <Button classId="secondary" text="Ok"  onClick={this.select} />
         </div>
    )
    return (
    <Popup title="Continue?" loading={false} buttons={buttons}>
        Do you want to continue with the next episode: "{this.props.title}"?
    </Popup>
    )
  }
};
export default ContinueNextEpisodePopup;
