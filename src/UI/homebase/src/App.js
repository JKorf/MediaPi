import React, {Component} from 'react';
import { BrowserRouter as Router, Route } from "react-router-dom";
import axios from 'axios';

import Header from './Modules/Header'
import Footer from './Modules/Footer'
import View from './Modules/Views/View.js'
import DashboardView from './Modules/Views/DashboardView.js'
import LoginPopup from './Modules/Components/Popups/LoginPopup.js'

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
import UrlView from './Modules/Views/MediaPlayer/UrlView.js'

import HomeDashboardView from './Modules/Views/Home/HomeDashboardView.js'
import HeatingView from './Modules/Views/Home/HeatingView.js'
import GasView from './Modules/Views/Home/GasView.js'
import PowerView from './Modules/Views/Home/PowerView.js'
import DevicesView from './Modules/Views/Home/DevicesView.js'
import DeviceView from './Modules/Views/Home/DeviceView.js'
import RulesView from './Modules/Views/Home/RulesView.js'
import RuleView from './Modules/Views/Home/RuleView.js'
import AutomationView from './Modules/Views/Home/AutomationView.js'
import AutomationGroupView from './Modules/Views/Home/AutomationGroupView.js'
import AutomationDeviceView from './Modules/Views/Home/AutomationDeviceView.js';

import ConfigurationDashboardView from './Modules/Views/Configuration/ConfigurationDashboardView.js'
import TestView from './Modules/Views/Configuration/TestView.js'
import ClientsView from './Modules/Views/Configuration/ClientsView.js'
import ClientView from './Modules/Views/Configuration/ClientView.js'

import Socket2 from './Socket2.js'
import PopupController from './Modules/PopupController.js'

import './Styles/base.less';
import './Styles/components.less';
import './Styles/mediaplayer.less';
import './Styles/rules.less';
import './Styles/settings.less';
import './Styles/automation.less';

class App extends Component {
  constructor(props) {
    super(props);

    this.state = {backConfig: {to:"/"}, auth: false};
    this.infoMessageRef = React.createRef();

    this.changeBack = this.changeBack.bind(this);
    this.changeTitle = this.changeTitle.bind(this);
    this.changeRightImage = this.changeRightImage.bind(this);

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

  componentWillMount()
  {
    var local = true;
    var location = window.location.hostname;

    if (!local){
        window.vars = {
            websocketBase: "https://api." + location + "/UI",
            apiBase: "https://api." + location + "/"
        };
    }
    else
    {
        var port = 50021;
        window.vars = {
            websocketBase: "http://" + location + ":" + port + "/UI",
            apiBase: "http://" + location + ":" + port + "/"
        };
    }

    Socket2.init();
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
        return <LoginPopup onAuthorize={(e)=> this.setState({auth: true})}/>;
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
                    <Route path="/mediaplayer/url" exact render={(props) => <UrlView {...props} functions={this.functions}  />} />

                    <Route path="/mediaplayer/history" exact render={(props) => <HistoryView {...props} functions={this.functions}  />} />

                    <Route path="/home/" exact render={(props) => <HomeDashboardView {...props} functions={this.functions}  />} />
                    <Route path="/home/heating" exact render={(props) => <HeatingView {...props} functions={this.functions}  />} />
                    <Route path="/home/gas" exact render={(props) => <GasView {...props} functions={this.functions}  />} />
                    <Route path="/home/power" exact render={(props) => <PowerView {...props} functions={this.functions}  />} />
                    <Route path="/home/devices" exact render={(props) => <DevicesView {...props} functions={this.functions}/>} />
                    <Route path="/home/device/:id" exact render={(props) => <DeviceView {...props} functions={this.functions}  />} />
                    <Route path="/home/rules" exact render={(props) => <RulesView {...props} functions={this.functions}  />} />
                    <Route path="/home/rule/:id" exact render={(props) => <RuleView {...props} functions={this.functions}  />} />
                    <Route path="/home/automation" exact render={(props) => <AutomationView {...props} functions={this.functions}  />} />
                    <Route path="/home/automation-group/:id" exact render={(props) => <AutomationGroupView {...props} functions={this.functions}  />} />
                    <Route path="/home/automation-device/:id" exact render={(props) => <AutomationDeviceView {...props} functions={this.functions}  />} />

                    <Route path="/configuration" exact render={(props) => <ConfigurationDashboardView {...props} functions={this.functions}  />} />
                    <Route path="/configuration/test" exact render={(props) => <TestView {...props} functions={this.functions}  />} />
                    <Route path="/configuration/clients" exact render={(props) => <ClientsView {...props} functions={this.functions}  />} />
                    <Route path="/configuration/clients/:id" exact render={(props) => <ClientView {...props} functions={this.functions}  />} />
                </View>
                <Footer functions={this.functions} />
                <PopupController ref={this.popupControllerRef} />
          </div>
      </Router>
    );
  }
};

export default App;


