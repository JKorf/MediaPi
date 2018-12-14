import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";
import axios from 'axios'

import View from './../View'

import ShowView from './../ShowView'
import MoviesView from './../MoviesView'
import MediaPlayerDashboardView from './../MediaPlayerDashboardView'


class MediaPlayerView extends Component {
  constructor(props) {
    super(props);
  }

  componentDidMount() {
  }

  render() {
    return (
    <div className="view-wrapper">
      <View>
         <Route path="/mediaplayer/" exact component={MediaPlayerDashboardView} />
         <Route path="/mediaplayer/shows" component={ShowView} />
         <Route path="/mediaplayer/movies" component={MoviesView} />
       </View>
    </div>
    );
  }
};

export default MediaPlayerView;