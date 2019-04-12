import React, { Component } from 'react';
import Popup from "./Popup.js"
import Button from "./../Button"

class SelectConditionPopup extends Component {
  constructor(props) {
    super(props);

    this.state = {selectedType: this.props.conditionTypes[0].id};
    this.cancel = this.cancel.bind(this);
    this.select = this.select.bind(this);
  }

  cancel()
  {
    this.props.onCancel();
  }

  select()
  {
    this.props.onSelect(this.state.selectedType);
  }

  render() {
    const buttons = (
        <div>
         <Button classId="secondary" text="Cancel" onClick={this.cancel} />
         <Button classId="secondary" text="Select"  onClick={this.select} />
         </div>
    )
    return (
    <Popup title="New condition type" loading={false} buttons={buttons}>
        Condition type:
        <select defaultValue={this.props.conditionTypes[0].id} onChange={(e) => this.setState({selectedType: e.target.value})}>
            { this.props.conditionTypes.map(type => <option value={type.id} key={type.id}>{type.name}</option>) }
        </select>
    </Popup>
    )
  }
};
export default SelectConditionPopup;
