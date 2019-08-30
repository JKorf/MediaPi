import React, { Component } from 'react';


class SearchBox extends Component {
  render() {
    return <input placeholder={this.props.placeholder} type="text" value={this.props.searchTerm} onChange={(e) => this.props.onChange(e.target.value)}/>
  }
}

export default SearchBox;