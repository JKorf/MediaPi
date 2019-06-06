import React, { Component } from 'react';
import axios from 'axios';
import { Link } from "react-router-dom";

import MediaPlayerView from './MediaPlayerView.js';
import Button from './../../Components/Button';
import SvgImage from './../../Components/SvgImage';
import ColorIndicator from './../../Components/ColorIndicator';
import ViewLoader from './../../Components/ViewLoader/ViewLoader'

import favoriteImage from './../../../Images/favorite.svg';
import favoriteFullImage from './../../../Images/favorite-full.svg';
import seenImage from './../../../Images/watched.svg';

class YouTubeVideoView extends Component {
  constructor(props) {
    super(props);
    this.viewRef = React.createRef();

    this.state = {loading: true};
    this.props.functions.changeBack({to: "/mediaplayer/youtube/" });
    this.props.functions.changeRightImage(null);

    this.play = this.play.bind(this);
    this.playVideo = this.playVideo.bind(this);

  }

  componentDidMount() {
    axios.get(window.vars.apiBase + 'youtube/video?id=' + this.props.match.params.id).then(data => {
        console.log(data.data);
        this.setState({video: data.data, loading: false});
        this.props.functions.changeTitle(data.data.title);
    }, err => {
        this.setState({ loading: false});
        console.log(err);
    });
  }

  play(position){
  // Fix
    this.viewRef.current.play({title: this.state.video.title, position: position});
  }

  playVideo(instance, video)
  {
    if(video.position !== 0)
        console.log("Continue from " + video.position);
    this.setState({loading: true});
    axios.post(window.vars.apiBase + 'play/youtube?instance=' + instance
        + "&url=" + encodeURIComponent(this.state.video.url)
        + "&title=" + encodeURIComponent(this.state.video.title)
        + "&position=" + video.position).then(
            () => this.setState({loading: false}),
            () => this.setState({loading: false})
        );
  }

  render() {

    return (
        <MediaPlayerView ref={this.viewRef} playMedia={this.playVideo}>
          <ViewLoader loading={this.state.loading}/>
          { this.state.video &&
              <div className="show">
                <div className="show-image">
                    <img alt="Show poster" src={this.state.video.poster} />
                </div>
                <div className="show-details">
                    <div className="label-row">
                        <div className="label-field">Airs</div>
                        <div className="label-value"></div>
                    </div>
                </div>
                <div className="show-synopsis">
                    {this.state.video.description}
                </div>

                <div className="movie-play-buttons">
                { this.state.video.played_for > 1000 * 60 &&
                    <Button text={"Continue from " + this.writeTimespan(this.state.video.played_for)} onClick={(e) => this.play( this.state.video.played_for)} classId="secondary"></Button>
                }
                <Button text={"Play" } onClick={(e) => this.play(0)} classId="secondary" />
              </div>
          </div>
          }
      </MediaPlayerView>
    );
  }
};

export default YouTubeVideoView;