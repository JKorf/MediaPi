import React, { Component } from 'react';


class SearchBox extends Component {
  constructor(props) {
    super(props);

    this.state = {value: ""};

    this.valueChange = this.valueChange.bind(this);
    this.triggerChange = this.triggerChange.bind(this);
  }

  componentDidMount(){
  }

  componentWillUnmount(){
  }

  valueChange(e){
    this.setState({value: e.target.value});
    if (this.timer)
        clearTimeout(this.timer);
    this.timer = setTimeout(this.triggerChange, 800);
  }

  triggerChange(){
    this.props.onChange(this.state.value);
  }

  render() {
    return <input type="text" value={this.state.value} onChange={this.valueChange}/>
  }
}

export default SearchBox;