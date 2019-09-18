import React, { Component } from 'react';
import axios from 'axios';

class DeviceGroupSelector extends Component {
  constructor(props) {
    super(props);
    this.state = {items: []};

    this.changeValue = this.changeValue.bind(this);
  }

  componentDidMount()
  {
    var subject = this.props.type === "group" ? "groups": "devices"

    axios.get(window.vars.apiBase + 'home/get_' + subject).then(
        (data) => {
            data = data.data;
            console.log(data);
            if (this.props.filter)
                data = data.filter(this.props.filter);

            this.setState({items: data});
            if (!this.props.value)
                this.changeValue(data[0].id);
         },
        (error) => { console.log(error) }
    )
  }

  changeValue(newValue)
  {
    this.props.onChange(newValue);
  }

  render(){
    return (
      <div className="light-group-selector">
        <select onChange={(e) => this.changeValue(e.target.value)} value={this.props.value}>
            { this.state.items.map(item => <option key={item.id} value={item.id}>{item.name}</option>) }
        </select>
      </div>)
  }
}

export default DeviceGroupSelector;