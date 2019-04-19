import React, { Component } from 'react';
import axios from 'axios';

class TradfriGroupSelector extends Component {
  constructor(props) {
    super(props);
    this.state = {groups: []};

    this.changeValue = this.changeValue.bind(this);
  }

  componentDidMount()
  {
    axios.get(window.vars.apiBase + 'tradfri/groups').then(
        (data) => {
            data = data.data;
            console.log(data);
            this.setState({groups: data});
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
            { this.state.groups.map(group => <option key={group.id} value={group.id}>{group.name}</option>) }
        </select>
      </div>)
  }
}

export default TradfriGroupSelector;