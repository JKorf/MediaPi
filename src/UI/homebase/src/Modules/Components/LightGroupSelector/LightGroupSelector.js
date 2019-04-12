import React, { Component } from 'react';
import axios from 'axios';

class LightGroupSelector extends Component {
  constructor(props) {
    super(props);
    this.state = {lights: []};

    this.changeValue = this.changeValue.bind(this);
  }

  componentDidMount()
  {
    axios.get(window.vars.apiBase + 'lighting/groups').then(
        (data) => {
            data = data.data;
            console.log(data);
            this.setState({lights: data});
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
            { this.state.lights.map(lightGroup => <option key={lightGroup.id} value={lightGroup.id}>{lightGroup.name}</option>) }
        </select>
      </div>)
  }
}

export default LightGroupSelector;