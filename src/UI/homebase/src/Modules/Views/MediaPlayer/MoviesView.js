import React, { Component } from 'react';
import axios from 'axios'

import MediaOverview from './../../MediaList/MediaOverview.js'
import View from './../View.js'

class MoviesView extends Component {
  constructor(props) {
    super(props);
    this.props.changeBack({to: "/mediaplayer/"});
  }

  componentDidMount() {

  }

  render() {
    return (
      <div>
        Movies
      </div>
    );
  }
};

export default MoviesView;