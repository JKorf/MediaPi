import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";
import axios from 'axios'

import View from './../View'

import ShowsView from './../ShowsView'
import ShowView from './../ShowView'
import MoviesView from './../MoviesView'
import MediaPlayerDashboardView from './../MediaPlayerDashboardView'
import Footer from './../../Footer'


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
         <Route path="/mediaplayer/shows" exact component={ShowsView} />
         <Route path='/mediaplayer/shows/:id' component={ShowView} />
         <Route path="/mediaplayer/movies" exact component={MoviesView} />
       </View>
       <Footer>
        Footer
       </Footer>
    </div>
    );
  }
};

export default MediaPlayerView;