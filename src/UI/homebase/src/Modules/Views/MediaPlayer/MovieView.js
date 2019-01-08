import React, { Component } from 'react';
import axios from 'axios';

import View from './../View.js';
import MediaPlayerView from './MediaPlayerView.js'

import Button from './../../Components/Button';
import SelectInstancePopup from './../../Components/Popups/SelectInstancePopup'
import Popup from './../../Components/Popups/Popup'

class MovieView extends Component {
  constructor(props) {
    super(props);
    this.viewRef = React.createRef();
    this.state = {movie: {images:[], rating: {}, torrents: {en: {}}}};
    this.props.changeBack({to: "/mediaplayer/movies/" });

    this.playMedia = this.playMedia.bind(this);
    this.play_torrent = this.play_torrent.bind(this);
    this.play_trailer = this.play_trailer.bind(this);
  }

  componentDidMount() {
    axios.get('http://localhost/movies/get_movie?id=' + this.props.match.params.id).then(data => {
        this.viewRef.current.changeState(1);
        console.log(data.data);
        this.props.changeTitle(data.data.title);
        this.setState({movie: data.data});
    }, err =>{
        this.viewRef.current.changeState(1);
        console.log(err);
        this.setState({loading: false});
    });
  }

  play_torrent(torrent){
    this.viewRef.current.play({type: "torrent", url: torrent.url, title: this.state.movie.title});
  }

  play_trailer(url){
      this.viewRef.current.play({type: "trailer", url: url, title: this.state.movie.title + " Trailer"});
  }

  playMedia(instance, media)
  {
    this.viewRef.current.changeState(0);
    if(media.type == "trailer"){
        axios.post('http://localhost/play/url?instance=' + instance
            + "&url=" + encodeURIComponent(media.url)
            + "&title=" + encodeURIComponent(this.state.movie.title + " Trailer"))
            .then(
                () => this.viewRef.current.changeState(1),
                ()=> this.viewRef.current.changeState(1)
            );
    }else{
        axios.post('http://localhost/play/movie?instance=' + instance
            + "&url=" + encodeURIComponent(media.url)
            + "&id=" + this.state.movie.id
            + "&title=" + encodeURIComponent(this.state.movie.title)
            + "&img=" + encodeURIComponent(this.state.movie.images.poster))
            .then(
                () => this.viewRef.current.changeState(1),
                ()=> this.viewRef.current.changeState(1)
            );
    }
  }

  render() {
    const movie = this.state.movie;
    const releaseDate = new Date();
    const torrents = Object.entries(movie.torrents.en).sort((a, b) => a[0] < b[0]);
    if (movie.released)
        releaseDate.setTime(movie.released * 1000);
    const releaseString = new Intl.DateTimeFormat('en-GB', { year: 'numeric', month: 'short', day: '2-digit' }).format(releaseDate);
    const showPopup = this.state.showPopup;
    const loading = this.state.loading;

    return (
        <MediaPlayerView ref={this.viewRef} playMedia={this.playMedia}>
          <div className="movie">
            <div className="movie-image">
                <img src={movie.images.poster} />
            </div>
            <div className="movie-details">
                <div className="label-row">
                    <div className="label-field">Released</div>
                    <div className="label-value">{releaseString}</div>
                </div>
                <div className="label-row">
                    <div className="label-field">Length</div>
                    <div className="label-value">{movie.runtime} minutes</div>
                </div>
                <div className="label-row">
                    <div className="label-field">Rating</div>
                    <div className="label-value">{movie.rating.percentage}%</div>
                </div>
            </div>
            <div className="movie-synopsis">
                {movie.synopsis}
            </div>
            <div className="movie-play-buttons">
                <Button text="Play trailer" onClick={(e) => this.play_trailer(movie.trailer)} classId="secondary"/>
                { torrents.map(([res, torrent]) => <Button key={res} text={"Play " + res } onClick={(e) => this.play_torrent(torrent)} classId="secondary" />)}
            </div>

            { showPopup &&
                <SelectInstancePopup onCancel={this.instanceSelectCancel} onSelect={this.instanceSelect} />
            }
            { loading &&
                <Popup loading={loading} />
            }
          </div>
        </MediaPlayerView>
    );
  }
};

export default MovieView;