import React, { Component } from 'react';
import axios from 'axios';

class MoodSelector extends Component {
  constructor(props) {
    super(props);
    this.state = {items: []};

    this.changeValue = this.changeValue.bind(this);
  }

  componentDidMount()
  {
    axios.get(window.vars.apiBase + 'home/moods').then(
        (data) => {
            data = data.data;
            console.log(data);
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
      <div className="mood-selector">
        <select onChange={(e) => this.changeValue(e.target.value)} value={this.props.value}>
            { this.state.items.map(item => <option key={item.id} value={item.id}>{item.name}</option>) }
        </select>
      </div>)
  }
}

export default MoodSelector;