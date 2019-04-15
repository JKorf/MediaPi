import React, { Component } from 'react';
import axios from 'axios';
import Socket from "./../../../Socket2.js"


class InstanceSelector extends Component {
  constructor(props) {
    super(props);
    this.state = {slaveData: []};

    this.slaveUpdate = this.slaveUpdate.bind(this);
    this.changeValue = this.changeValue.bind(this);
  }

  componentDidMount()
  {
    this.slaveSub = Socket.subscribe("slaves", this.slaveUpdate);
  }

  componentWillUnmount()
  {
    Socket.unsubscribe(this.slaveSub);
  }

  changeValue(newValue)
  {
    this.props.onChange(newValue);
  }

  slaveUpdate(subId, data){
    console.log(data);
    this.setState({slaveData: data});
    this.changeValue(data[0].id);
  }

  render(){
    return (
      <div className="instance-selector">
        <select value={this.props.value} onChange={(e) => this.changeValue(e.target.value)}>
        {
            this.state.slaveData.map(slave => <option key={slave.id} value={slave.id}>{slave.name}</option>)
        }
        </select>
      </div>)
  }
}

export default InstanceSelector;