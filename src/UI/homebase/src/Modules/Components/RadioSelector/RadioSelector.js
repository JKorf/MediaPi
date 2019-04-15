import React, { Component } from 'react';
import axios from 'axios';

class RadioSelector extends Component {
  constructor(props) {
    super(props);
    this.state = {radios: []};

    this.changeValue = this.changeValue.bind(this);
  }

  componentDidMount()
  {
    axios.get(window.vars.apiBase + 'radios').then(
        (data) => {
            data = data.data;
            console.log(data);
            this.setState({radios: data});
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
      <div className="radio-selector">
        <select onChange={(e) => this.changeValue(e.target.value)} value={this.props.value}>
            { this.state.radios.map(radio => <option key={radio.id} value={radio.id}>{radio.title}</option>) }
        </select>
      </div>)
  }
}

export default RadioSelector;