import React, { Component } from 'react';
import axios from 'axios';
import { Link } from "react-router-dom";

import MediaPlayerView from './MediaPlayerView.js';
import Button from './../../Components/Button';
import SvgImage from './../../Components/SvgImage';
import ColorIndicator from './../../Components/ColorIndicator';
import ViewLoader from './../../Components/ViewLoader/ViewLoader'
import FadeBox from './../../Components/FadeBox'

import favoriteImage from './../../../Images/favorite.svg';
import favoriteFullImage from './../../../Images/favorite-full.svg';
import seenImage from './../../../Images/watched.svg';
import likeImage from './../../../Images/like.svg';
import dislikeImage from './../../../Images/dislike.svg';

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
        console.log(data.data.description);
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

   writeTimespan(duration)
  {
     duration = Math.round(duration);
     var seconds = parseInt((duration / 1000) % 60),
      minutes = parseInt((duration / (1000 * 60)) % 60),
      hours = parseInt((duration / (1000 * 60 * 60)) % 24);

      hours = (hours < 10) ? "0" + hours : hours;
      minutes = (minutes < 10) ? "0" + minutes : minutes;
      seconds = (seconds < 10) ? "0" + seconds : seconds;

      if (hours > 0)
        return hours + ":" + minutes + ":" + seconds;
      return minutes + ":" + seconds;
  }

  parseLength(data){
     var a = data.match(/\d+H|\d+M|\d+S/g),
        result = 0;

    var d = { 'H': 3600, 'M': 60, 'S': 1 },
        num,
        type;

    for (var i = 0; i < a.length; i++) {
        num = a[i].slice(0, a[i].length - 1);
        type = a[i].slice(a[i].length - 1, a[i].length);
        result += num + ":";
    }
    if (result[0] == "0")
        result = result.substring(1, result.length);

    return result.substring(0, result.length-1);
  }

  render() {

    return (
        <MediaPlayerView ref={this.viewRef} playMedia={this.playVideo}>
          <ViewLoader loading={this.state.loading}/>
          { this.state.video &&
              <div className="show">
                <div className="youtube-image">
                    <img alt="Show poster" src={this.state.video.poster} />
                </div>
                <div className="youtube-details">
                    <div className="label-row youtube-stats-row">
                        <div className="label-field">
                            <div className="youtube-stats-img"><SvgImage src={seenImage} /></div>
                            <div className="youtube-stats-text">{this.state.video.views}</div>
                        </div>
                        <div className="label-value">
                            <div className="youtube-stats-col">
                                <div className="youtube-stats-img"><SvgImage src={likeImage} /></div>
                                <div className="youtube-stats-text">{this.state.video.likes}</div>
                            </div>
                            <div className="youtube-stats-col">
                                <div className="youtube-stats-img"><SvgImage src={dislikeImage} /></div>
                                <div className="youtube-stats-text">{this.state.video.dislikes}</div>
                            </div>
                        </div>
                    </div>
                    <div className="label-row">
                        <div className="label-field">Uploaded</div>
                        <div className="label-value">{new Intl.DateTimeFormat('en-GB', { year: 'numeric', month: 'short', day: '2-digit', hour:'2-digit', minute: '2-digit' }).format(Date.parse(this.state.video.upload_date))}</div>
                    </div>
                    <div className="label-row">
                        <div className="label-field">Channel</div>
                        <div className="label-value">{this.state.video.channel_title}</div>
                    </div>
                    <div className="label-row">
                        <div className="label-field">Duration</div>
                        <div className="label-value">{this.parseLength(this.state.video.duration)}</div>
                    </div>
                </div>

                <div className="youtube-synopsis" dangerouslySetInnerHTML={{__html: this.state.video.description}}>
                </div>

                <div className="movie-play-buttons">
                { this.state.video.played_for > 1000 * 5 &&
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