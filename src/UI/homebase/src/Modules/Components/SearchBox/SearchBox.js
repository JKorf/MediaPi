import React, { Component } from 'react';


class SearchBox extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    return <input type="text" value={this.props.searchTerm} onChange={(e) => this.props.onChange(e.target.value)}/>
  }
}

export default SearchBox;