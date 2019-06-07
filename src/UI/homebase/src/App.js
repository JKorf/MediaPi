/*eslint no-mixed-operators: "off"*/

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
import YouTubeMainView from './Modules/Views/MediaPlayer/YouTubeMainView.js'
import YouTubeVideoView from './Modules/Views/MediaPlayer/YouTubeVideoView.js'
import YouTubeChannelView from './Modules/Views/MediaPlayer/YouTubeChannelView.js'
import HistoryView from './Modules/Views/MediaPlayer/HistoryView.js'

import HomeDashboardView from './Modules/Views/Home/HomeDashboardView.js'
import HeatingView from './Modules/Views/Home/HeatingView.js'
import GasView from './Modules/Views/Home/GasView.js'
import PowerView from './Modules/Views/Home/PowerView.js'
import TradfriView from './Modules/Views/Home/TradfriView.js'
import DevicesView from './Modules/Views/Home/DevicesView.js'
import DeviceView from './Modules/Views/Home/DeviceView.js'
import RulesView from './Modules/Views/Home/RulesView.js'
import RuleView from './Modules/Views/Home/RuleView.js'

import SettingsView from './Modules/Views/SettingsView.js'

import Socket2 from './Socket2.js'
import PopupController from './Modules/PopupController.js'

import './Styles/base.less';
import './Styles/components.less';
import './Styles/mediaplayer.less';
import './Styles/rules.less';

class App extends Component {
  constructor(props) {
    super(props);

    this.state = {backConfig: {to:"/"}, auth: false};
    this.infoMessageRef = React.createRef();

    this.changeBack = this.changeBack.bind(this);
    this.changeTitle = this.changeTitle.bind(this);
    this.changeRightImage = this.changeRightImage.bind(this);
    this.processLoginResult = this.processLoginResult.bind(this);
    this.processRefreshResult = this.processRefreshResult.bind(this);
    this.setSessionKey = this.setSessionKey.bind(this);

    this.popupControllerRef = React.createRef();

    this.functions = {
        changeBack: this.changeBack,
        changeTitle: this.changeTitle,
        changeRightImage: this.changeRightImage,
        showPopup: (popup) => this.popupControllerRef.current.showPopup(popup),
        closePopup: (popup) => this.popupControllerRef.current.closePopup(popup),
    }

    axios.interceptors.request.use(request => {
      request.headers['Session-Key'] = sessionStorage.getItem('Session-Key');
      return request
    });
  }

  componentWillMount() {

    var apiPort = 50021;
    var location = window.location.hostname + ":" + apiPort;
    window.vars = {
        apiPort: 50021,
        websocketBase: "ws://" + location + "/UI",
        apiBase: "http://" + location + "/"
    };

    Socket2.init();
    this.authenticate();
  }

  authenticate()
  {
    var clientId = localStorage.getItem('Client-ID');
    if (!clientId){
        clientId = this.generate_id();
        localStorage.setItem('Client-ID', clientId);
        axios.defaults.headers.common['Client-ID'] = clientId;
        this.login();
    }
    else{
        axios.defaults.headers.common['Client-ID'] = clientId;
        this.refresh();
    }
  }

  login()
  {
    var pw = prompt("Password");
    if (pw)
        axios.post(window.vars.apiBase + "auth/login?p=" + encodeURIComponent(pw)).then(this.processLoginResult, this.processLoginResult);
  }

  refresh()
  {
    axios.post(window.vars.apiBase + "auth/refresh").then(this.processRefreshResult, this.processRefreshResult);
  }

  generate_id()
  {
      return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
        (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
      )
  }

  processLoginResult(result)
  {
    if (result.response)
        result = result.response;

    if(!result.status)
    {
        this.setState({authError: "No connection could be made to server"});
    }
    else if(result.status === 200)
    {
        console.log("Successfully logged in");
        this.setSessionKey(result.data.key);
    }
    else if(result.status === 401)
    {
        console.log("Login failed");
        this.login();
    }
    else{
        this.setState({authError: "Error during login: " + result.statusText});
    }
  }

  processRefreshResult(result)
  {
    if (result.response)
        result = result.response;

    if(!result.status)
    {
        this.setState({authError: "No connection could be made to server"});
    }
    else if(result.status === 200)
    {
        console.log("Successfully refreshed");
        this.setSessionKey(result.data.key);
    }
    else if(result.status === 401)
    {
        console.log("Refresh failed, need to log in again");
        this.login();
    }
    else{
        this.setState({authError: "Error during authentication: " + result.statusText});
    }
  }

  setSessionKey(key){
    sessionStorage.setItem('Session-Key', key);
    Socket2.connect();
    this.setState({auth: true});
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
        if (this.state.authError) return <div>Authentication failed: {this.state.authError}</div>
        else  return <div>Authentication required</div>
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
                    <Route path="/mediaplayer/youtube" exact render={(props) => <YouTubeMainView {...props} functions={this.functions}  />} />
                    <Route path="/mediaplayer/youtube/v/:id" exact render={(props) => <YouTubeVideoView {...props} functions={this.functions}  />} />
                    <Route path="/mediaplayer/youtube/c/:id" exact render={(props) => <YouTubeChannelView {...props} functions={this.functions}  />} />

                    <Route path="/mediaplayer/history" exact render={(props) => <HistoryView {...props} functions={this.functions}  />} />

                    <Route path="/home/" exact render={(props) => <HomeDashboardView {...props} functions={this.functions}  />} />
                    <Route path="/home/heating" exact render={(props) => <HeatingView {...props} functions={this.functions}  />} />
                    <Route path="/home/gas" exact render={(props) => <GasView {...props} functions={this.functions}  />} />
                    <Route path="/home/power" exact render={(props) => <PowerView {...props} functions={this.functions}  />} />
                    <Route path="/home/tradfri" exact render={(props) => <TradfriView {...props} functions={this.functions}  />} />
                    <Route path="/home/devices" exact render={(props) => <DevicesView {...props} functions={this.functions}/>} />
                    <Route path="/home/device/:id" exact render={(props) => <DeviceView {...props} functions={this.functions}  />} />
                    <Route path="/home/rules" exact render={(props) => <RulesView {...props} functions={this.functions}  />} />
                    <Route path="/home/rule/:id" exact render={(props) => <RuleView {...props} functions={this.functions}  />} />

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


