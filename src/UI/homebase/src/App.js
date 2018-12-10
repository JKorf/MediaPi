import React from 'react';

import Header from './Modules/Layout/Header'
import Footer from './Modules/Layout/Footer'
import View from './Modules/Layout/View'
import ShowView from './Modules/ShowView'
import Player from './Modules/Player'

import './Modules/base.css';

const App = () => (
  <div className="App">
        <Header name="Jan" age="26"/>
        <View>
            <Player />
            <ShowView />

        </View>
        <Footer />
      </div>
);

export default App;


