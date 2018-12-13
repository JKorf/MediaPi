import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";
import axios from 'axios'

import View from './../View'
import Footer from './../../Footer'

import ShowView from './../ShowView'
import MoviesView from './../MoviesView'


class MediaPlayerView extends Component {
  constructor(props) {
    super(props);
  }

  componentDidMount() {
  }

  render() {
    return (
    <div class="view-wrapper">
      <View>
         <Route path="/mediaplayer/shows" exact component={ShowView} />
         <Route path="/mediaplayer/movies" exact component={MoviesView} />
       </View>
        <Footer>
            <Link to="/mediaplayer/shows">Shows</Link> | <Link to="/mediaplayer/movies">Movies</Link>
        </Footer>
    </div>
    );
  }
};

export default MediaPlayerView;