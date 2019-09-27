import React, { Component } from 'react';
import Popup from "./Popup.js"
import Button from "./../Button"

class AddMoodPopup extends Component {
  constructor(props) {
    super(props);
    this.state = {name: ""};
    this.cancel = this.cancel.bind(this);
    this.add = this.add.bind(this);
  }

  cancel()
  {
    this.props.onCancel();
  }

  add()
  {
    this.props.onAdd(this.state.name);
  }

  render() {
    const buttons = (
        <div>
         <Button classId="secondary" text="Cancel" onClick={this.cancel} />
         <Button classId="secondary" text="Add" onClick={this.add} />
         </div>
    )
    return (
    <Popup title="Create a new mood" loading={false} buttons={buttons} classId="select-media-popup">
        <div className="mood-popup-input">
            <input type="text" placeholder="Mood name" value={this.state.name} onChange={e => this.setState({name: e.target.value})} />
        </div>
    </Popup>
    )
  }
};
export default AddMoodPopup;
