import React, { Component } from 'react';

import DashboardLink from './../../Components/DashboardLink'
import showImg from './../../../Images/show.svg'
import movieImg from './../../../Images/movie.svg'
import hdImg from './../../../Images/hd.svg'
import torrentImg from './../../../Images/link.svg'
import radioImg from './../../../Images/radio.svg'
import youtubeImg from './../../../Images/youtube.svg'
import playImg from './../../../Images/play.svg'
import historyImg from './../../../Images/history.svg'

class MediaPlayerDashboardView extends Component {
  constructor(props) {
    super(props);
    this.props.functions.changeBack({});
    this.props.functions.changeTitle("Media");
    this.props.functions.changeRightImage(null);
  }

  componentDidMount() {
  }

  render() {
    return (
    <div className="mediaplayer-dashboard">
        <DashboardLink to="/mediaplayer/shows" img={showImg} text="shows"></DashboardLink>
        <DashboardLink to="/mediaplayer/movies" img={movieImg} text="movies"></DashboardLink>
        <DashboardLink to="/mediaplayer/hd" img={hdImg} text="hard disk"></DashboardLink>
        <DashboardLink to="/mediaplayer/torrents" img={torrentImg} text="torrents"></DashboardLink>
        <DashboardLink to="/mediaplayer/radio" img={radioImg} text="radio"></DashboardLink>
        <DashboardLink to="/mediaplayer/youtube" img={youtubeImg} text="youtube"></DashboardLink>
        <DashboardLink to="/mediaplayer/players" img={playImg} text="players"></DashboardLink>
        <DashboardLink to="/mediaplayer/history" img={historyImg} text="history"></DashboardLink>
    </div>
    );
  }
};

export default MediaPlayerDashboardView;