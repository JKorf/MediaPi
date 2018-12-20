import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";
import axios from 'axios'

import View from './../View.js'

import ShowsView from './ShowsView'
import ShowView from './ShowView'
import MoviesView from './MoviesView'
import HDView from './HDView'
import MediaPlayerDashboardView from './MediaPlayerDashboardView'
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
         <Route path="/mediaplayer/" exact render={(props) => <MediaPlayerDashboardView {...props} changeBack={this.props.changeBack}/>} />
         <Route path="/mediaplayer/shows" exact render={(props) => <ShowsView {...props} changeBack={this.props.changeBack}/>} />
         <Route path='/mediaplayer/shows/:id' render={(props) => <ShowView {...props} changeBack={this.props.changeBack} />} />
         <Route path="/mediaplayer/movies" exact render={(props) => <MoviesView {...props} changeBack={this.props.changeBack}/>} />
         <Route path="/mediaplayer/hd" exact render={(props) => <HDView {...props} changeBack={this.props.changeBack} />} />
       </View>
    </div>
    );
  }
};

export default MediaPlayerView;