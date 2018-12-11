import React, { Component } from 'react';
import View from './../../Layout/View'
import MediaPlayerWidget from './../../Widgets/MediaPlayerWidget'

class DashboardView extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <View>
        <MediaPlayerWidget />
        <MediaPlayerWidget />
      </View>
    );
  }
};

export default DashboardView;