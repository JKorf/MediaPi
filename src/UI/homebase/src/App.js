import React, {Component} from 'react';
import { BrowserRouter as Router, Route } from "react-router-dom";
import axios from 'axios';

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
import HistoryView from './Modules/Views/MediaPlayer/HistoryView.js'

import HomeDashboardView from './Modules/Views/Home/HomeDashboardView.js'
import HeatingView from './Modules/Views/Home/HeatingView.js'
import LightingView from './Modules/Views/Home/LightingView.js'

import SettingsView from './Modules/Views/SettingsView.js'

import Socket from './Socket.js'
import PopupController from './Modules/PopupController.js'

import './Styles/base.less';
import './Styles/mediaplayer.less';

class App extends Component {
  constructor(props) {
    super(props);

    this.state = {backConfig: {to:"/"}, auth: false};
    this.infoMessageRef = React.createRef();

    this.changeBack = this.changeBack.bind(this);
    this.changeTitle = this.changeTitle.bind(this);
    this.changeRightImage = this.changeRightImage.bind(this);
    this.processAuthResult = this.processAuthResult.bind(this);

    this.popupControllerRef = React.createRef();

    this.functions = {
        changeBack: this.changeBack,
        changeTitle: this.changeTitle,
        changeRightImage: this.changeRightImage,
        showPopup: (popup) => this.popupControllerRef.current.showPopup(popup),
        closePopup: (popup) => this.popupControllerRef.current.closePopup(popup),
    }
  }

  componentWillMount() {

    var apiPort = 50021;
    var location = window.location.hostname + ":" + apiPort;
    window.vars = {
        apiPort: 50021,
        websocketBase: "ws://" + location + "/ws",
        apiBase: "http://" + location + "/"
    };

    Socket.init();
    this.authenticate();
  }

  authenticate()
  {
    var key = localStorage.getItem('Auth-Key');
    if (key){
        axios.defaults.headers.common['Auth-Key'] = key;
        this.setState({auth: true});
    }
    else{
        var pw = prompt("Password");
        axios.post(window.vars.apiBase + "auth/init?p=" + encodeURIComponent(pw) + "&i=" + encodeURIComponent(this.generate_id())).then(this.processAuthResult, this.processAuthResult);
    }
  }

  generate_id()
  {
      return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
        (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
      )
  }

  processAuthResult(result)
  {
    if(result.data.success){
        localStorage.setItem('Auth-Key', result.data.key);
        axios.defaults.headers.common['Auth-Key'] =  result.data.key;
        Socket.connect();
        this.setState({auth: true});
    }
  }

  changeBack (value){
    this.setState({backConfig: value});
  }

  changeRightImage (value){
    this.setState({rightImage: value});
  }

  changeTitle (value){
    this.setState({title: value});
  }

  render() {
    if (!this.state.auth){
        return <div>Authentication failed</div>
    }

    const link = this.state.backConfig;
    return (
      <Router>
          <div className="app">
                <Header backConfig={link} title={this.state.title} rightImage={this.state.rightImage} />
                <View>
                    <Route path="/" exact render={(props) => <DashboardView {...props} functions={this.functions} />} />
                    <Route path="/mediaplayer/" exact render={(props) => <MediaPlayerDashboardView {...props} functions={this.functions} />} />
                    <Route path="/mediaplayer/shows" exact render={(props) => <ShowsView {...props} functions={this.functions} />} />
                    <Route path='/mediaplayer/shows/:id' render={(props) => <ShowView {...props} functions={this.functions}  />} />
                    <Route path="/mediaplayer/movies" exact render={(props) => <MoviesView {...props} functions={this.functions} />} />
                    <Route path="/mediaplayer/movies/:id" render={(props) => <MovieView {...props} functions={this.functions}/>} />
                    <Route path="/mediaplayer/hd" exact render={(props) => <HDView {...props} functions={this.functions}/>} />
                    <Route path="/mediaplayer/radio" exact render={(props) => <RadioView {...props} functions={this.functions}  />} />
                    <Route path="/mediaplayer/torrents" exact render={(props) => <TorrentView {...props} functions={this.functions}  />} />
                    <Route path="/mediaplayer/players" exact render={(props) => <PlayersView {...props} functions={this.functions}/>} />
                    <Route path="/mediaplayer/player/:id" exact render={(props) => <PlayerView {...props} functions={this.functions}  />} />
                    <Route path="/mediaplayer/history" exact render={(props) => <HistoryView {...props} functions={this.functions}  />} />

                    <Route path="/home/" exact render={(props) => <HomeDashboardView {...props} functions={this.functions}  />} />
                    <Route path="/home/heating" exact render={(props) => <HeatingView {...props} functions={this.functions}  />} />
                    <Route path="/home/lighting" exact render={(props) => <LightingView {...props} functions={this.functions}  />} />

                    <Route path="/settings" exact render={(props) => <SettingsView {...props} functions={this.functions}  />} />
                </View>
                <Footer functions={this.functions} />
                <PopupController ref={this.popupControllerRef} />
          </div>
      </Router>
    );
  }
};

export default App;


