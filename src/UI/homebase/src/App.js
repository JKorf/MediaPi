import React, {Component} from 'react';
import { BrowserRouter as Router, Route } from "react-router-dom";

import Header from './Modules/Header'
import Footer from './Modules/Footer'
import View from './Modules/Views/View.js'
import DashboardView from './Modules/Views/DashboardView.js'
import MediaPlayerDashboardView from './Modules/Views/MediaPlayer/MediaPlayerDashboardView.js'
import ShowsView from './Modules/Views/MediaPlayer/ShowsView.js'
import ShowView from './Modules/Views/MediaPlayer/ShowView.js'
import MoviesView from './Modules/Views/MediaPlayer/MoviesView.js'
import MovieView from './Modules/Views/MediaPlayer/MovieView.js'
import HDView from './Modules/Views/MediaPlayer/HDView.js'
import RadioView from './Modules/Views/MediaPlayer/RadioView.js'
import TorrentView from './Modules/Views/MediaPlayer/TorrentView.js'
import PlayersView from './Modules/Views/MediaPlayer/PlayersView.js'
import PlayerView from './Modules/Views/MediaPlayer/PlayerView.js'
import Socket from './Socket.js'
import PopupController from './Modules/PopupController.js'

import './Styles/base.less';
import './Styles/mediaplayer.less';

class App extends Component {
  constructor(props) {
    super(props);

    Socket.init();
    this.state = {backConfig: {to:"/"}};

    this.changeBack = this.changeBack.bind(this);
    this.changeTitle = this.changeTitle.bind(this);
  }

  changeBack (value){
    this.setState({backConfig: value});
  }

  changeTitle (value){
    this.setState({title: value});
  }

  render() {
    const link = this.state.backConfig;
    return (
      <Router>
          <div className="app">
                <Header backConfig={link} title={this.state.title} />
                <View>
                    <Route path="/" exact render={(props) => <DashboardView {...props} changeBack={this.changeBack} changeTitle={this.changeTitle} />} />
                    <Route path="/mediaplayer/" exact render={(props) => <MediaPlayerDashboardView {...props} changeBack={this.changeBack} changeTitle={this.changeTitle} />} />
                    <Route path="/mediaplayer/shows" exact render={(props) => <ShowsView {...props} changeBack={this.changeBack} changeTitle={this.changeTitle} />} />
                    <Route path='/mediaplayer/shows/:id' render={(props) => <ShowView {...props} changeBack={this.changeBack} changeTitle={this.changeTitle}  />} />
                    <Route path="/mediaplayer/movies" exact render={(props) => <MoviesView {...props} changeBack={this.changeBack} changeTitle={this.changeTitle} />} />
                    <Route path="/mediaplayer/movies/:id" render={(props) => <MovieView {...props} changeBack={this.changeBack} changeTitle={this.changeTitle} />} />
                    <Route path="/mediaplayer/hd" exact render={(props) => <HDView {...props} changeBack={this.changeBack}  changeTitle={this.changeTitle} />} />
                    <Route path="/mediaplayer/radio" exact render={(props) => <RadioView {...props} changeBack={this.changeBack} changeTitle={this.changeTitle}  />} />
                    <Route path="/mediaplayer/torrents" exact render={(props) => <TorrentView {...props} changeBack={this.changeBack} changeTitle={this.changeTitle}  />} />
                    <Route path="/mediaplayer/players" exact render={(props) => <PlayersView {...props} changeBack={this.changeBack}  changeTitle={this.changeTitle} />} />
                    <Route path="/mediaplayer/player/:id" exact render={(props) => <PlayerView {...props} changeBack={this.changeBack} changeTitle={this.changeTitle}  />} />
                </View>
                <Footer />
                <PopupController />
          </div>
      </Router>
    );
  }
};

export default App;


