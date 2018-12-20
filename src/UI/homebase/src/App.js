import React, {Component} from 'react';
import { BrowserRouter as Router, Route } from "react-router-dom";

import Header from './Modules/Header'
import Footer from './Modules/Footer'
import DashboardView from './Modules/Views/DashboardView'
import MediaPlayerView from './Modules/Views/MediaPlayer/MediaPlayerView'
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
                <Route path="/" exact component={DashboardView} />
                <Route path="/mediaplayer/" render={()=><MediaPlayerView changeBack={this.changeBack} />} />
                <Footer />
          </div>
      </Router>
    );
  }
};

export default App;


