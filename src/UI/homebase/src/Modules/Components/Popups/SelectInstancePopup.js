import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";
import Popup from "./Popup.js"
import Button from "./../Button"

import Socket from "./../../../Socket.js"

class SelectInstancePopup extends Component {
  constructor(props) {
    super(props);
    this.state = {slaveData: [], instance: 0, loading: true};

    this.slaveUpdate = this.slaveUpdate.bind(this);
    this.instanceChange = this.instanceChange.bind(this);
    this.cancel = this.cancel.bind(this);
    this.select = this.select.bind(this);
  }

  componentDidMount() {
  console.log("h");
    this.slaveSub = Socket.subscribe("slaves", this.slaveUpdate);
  }

  componentWillUnmount() {
    Socket.unsubscribe(this.slaveSub);
  }

  slaveUpdate(data){
    this.setState({slaveData: data});
    if (!this.state.instance)
        this.setState({instance: data[0].id});

    if (data.length == 1)
        this.select();
    else
        this.setState({loading: false});
  }

  instanceChange(event){
    this.setState({instance: event.target.value});
  }

  cancel()
  {
    this.props.onCancel();
    console.log("Cancel");
  }

  select()
  {
    this.props.onSelect(this.state.instance);
  }

  render() {
    const slaves = this.state.slaveData;
    const buttons = (
        <div>
         <Button classId="secondary" text="Cancel" onClick={this.cancel} />
         <Button classId="secondary" text="Select"  onClick={this.select} />
         </div>
    )
    return (
    <Popup title="Select a media player" loading={this.state.loading} onCancel={(e) => this.cancel(e)} onSelect={e => this.select(e)} buttons={buttons}>
        <div className="label-row">
            <div className="label-field">Player</div>
            <div className="label-value">
                <select value={this.state.instance} onChange={this.instanceChange}>
                {
                    slaves.map(slave => <option key={slave.id} value={slave.id}>{slave.name}</option>)
                }
                </select>
            </div>
        </div>
    </Popup>
    )
  }
};
export default SelectInstancePopup;
