import React, { Component } from 'react';
import axios from 'axios'

import DashboardLink from './../../../Components/DashboardLink'
import showImg from './../../../../Images/show.svg'
import movieImg from './../../../../Images/movie.svg'
import hdImg from './../../../../Images/hd.svg'
import torrentImg from './../../../../Images/link.svg'

class MediaPlayerDashboardView extends Component {
  constructor(props) {
    super(props);
    this.props.changeBack({to: "/mediaplayer/"});
  }

  componentDidMount() {
  }

  render() {
    return (
    <div className="mediaplayer-dashboard">
        <DashboardLink to="/mediaplayer/shows" img={showImg} text="Shows"></DashboardLink>
        <DashboardLink to="/mediaplayer/movies" img={movieImg} text="Movies"></DashboardLink>
        <DashboardLink to="/mediaplayer/hd" img={hdImg} text="Hard disk"></DashboardLink>
        <DashboardLink to="/mediaplayer/torrents" img={torrentImg} text="Torrents"></DashboardLink>
    </div>
    );
  }
};

export default MediaPlayerDashboardView;