import React, {Component} from 'react';

import Header from './Modules/Layout/Header'
import Footer from './Modules/Layout/Footer'
import View from './Modules/Layout/View'
import DashboardView from './Modules/Views/DashboardView'
import ShowView from './Modules/Views/ShowView'
import Socket from './Socket.js'

import './Modules/base.css';

class App extends Component {
  constructor(props) {
    super(props);

    Socket.init();
  }

  render() {
    return (
      <div className="App">
        <Header name="Jan" age="26"/>
        <DashboardView />
        <ShowView />
        <Footer />
      </div>
    );
  }
};

export default App;


