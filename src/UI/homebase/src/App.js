import React, {Component} from 'react';
import { BrowserRouter as Router, Route } from "react-router-dom";

import Header from './Modules/Header'
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
      <Router>
          <div className="app">
                <Header name="Jan" age="26"/>
                <Route path="/" exact component={DashboardView} />
                <Route path="/shows/" component={ShowView} />
          </div>
      </Router>
    );
  }
};

export default App;


