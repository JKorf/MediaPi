import React, { Component } from 'react';
import axios from 'axios'

import MediaOverview from './../../MediaList/MediaOverview'
import View from './../View'

class MoviesView extends Component {
  constructor(props) {
    super(props);
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