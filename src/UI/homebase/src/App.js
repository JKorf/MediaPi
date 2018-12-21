import React, {Component} from 'react';
import { BrowserRouter as Router, Route } from "react-router-dom";

import Header from './Modules/Header'
import Footer from './Modules/Footer'
import DashboardView from './Modules/Views/DashboardView.js'
import MediaPlayerDashboardView from './Modules/Views/MediaPlayer/MediaPlayerDashboardView.js'
import ShowsView from './Modules/Views/MediaPlayer/ShowsView.js'
import ShowView from './Modules/Views/MediaPlayer/ShowView.js'
import MoviesView from './Modules/Views/MediaPlayer/MoviesView.js'
import HDView from './Modules/Views/MediaPlayer/HDView.js'
import Socket from './Socket.js'

import './Styles/base.less';
import './Styles/mediaplayer.less';

class App extends Component {
  constructor(props) {
    super(props);

    Socket.init();
    this.state = {backConfig: {to:"/"}};

    this.changeBack = this.changeBack.bind(this);
  }

  changeBack (value){
    this.setState({backConfig: value});
  }

  render() {
    const link = this.state.backConfig;
    return (
      <Router>
          <div className="app">
                <Header backConfig={link} />
                <div className="view-wrapper">
                <Route path="/" exact component={DashboardView} />
                    <Route path="/mediaplayer/" exact render={(props) => <MediaPlayerDashboardView changeBack={this.changeBack}/>} />
                    <Route path="/mediaplayer/shows" exact render={(props) => <ShowsView changeBack={this.changeBack}/>} />
                    <Route path='/mediaplayer/shows/:id' render={(props) => <ShowView changeBack={this.changeBack} />} />
                    <Route path="/mediaplayer/movies" exact render={(props) => <MoviesView changeBack={this.changeBack}/>} />
                    <Route path="/mediaplayer/hd" exact render={(props) => <HDView changeBack={this.changeBack} />} />
                </div>
                <Footer />
          </div>
      </Router>
    );
  }
};

export default App;


