import React, {Component} from 'react';
import { BrowserRouter as Router, Route } from "react-router-dom";

import Header from './Modules/Header'
import DashboardView from './Modules/Views/DashboardView'
import MediaPlayerView from './Modules/Views/MediaPlayer/MediaPlayerView'
import Socket from './Socket.js'

import './Styles/base.less';
import './Styles/mediaplayer.less';

class App extends Component {
  constructor(props) {
    super(props);

    Socket.init();
  }

  render() {
    return (
      <Router>
          <div className="app">
                <Header/>
                <Route path="/" exact component={DashboardView} />
                <Route path="/mediaplayer/" component={MediaPlayerView} />
          </div>
      </Router>
    );
  }
};

export default App;


