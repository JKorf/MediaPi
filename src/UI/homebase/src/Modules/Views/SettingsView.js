import React, { Component } from 'react';
import ReactDOM from 'react-dom';

import axios from 'axios'

import View from './View.js'
import SvgImage from './../Components/SvgImage'
import TestWidget from './../Widgets/TestWidget.js'
import MediaPlayerWidget from './../Widgets/MediaPlayerWidget.js'
import FavoriteSeriesWidget from './../Widgets/FavoriteSeriesWidget.js'
import Socket from './../../Socket.js'
import { InfoGroup, InfoRow } from './../Components/InfoGroup'

import settingsImage from './../../Images/settings.svg';

class SettingsView extends Component {
  constructor(props) {
    super(props);

    this.props.functions.changeBack({});
    this.props.functions.changeTitle("Settings");
    this.props.functions.changeRightImage(null);
  }

  componentDidMount() {
  }

  componentWillUnmount() {
  }

  render() {
    return <div className="settings-view">
        <InfoGroup title="Appearance">
        </InfoGroup>
    </div>
  }
};

export default SettingsView;