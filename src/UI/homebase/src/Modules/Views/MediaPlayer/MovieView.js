import React, { Component } from 'react';
import axios from 'axios';
import { Link } from "react-router-dom";
import { writeTimespan, formatTime } from './../../../Utils/Util.js';

import MediaPlayerView from './MediaPlayerView.js'

import Button from './../../Components/Button';
import SelectInstancePopup from './../../Components/Popups/SelectInstancePopup'
import Popup from './../../Components/Popups/Popup'
import ViewLoader from './../../Components/ViewLoader/ViewLoader'

class MovieView extends Component {
  constructor(props) {
    super(props);
    this.viewRef = React.createRef();
    this.state = {movie: {images:[], rating: {}, torrents: {en: {}}}, loading: true};
    this.props.functions.changeBack({to: "/mediaplayer/movies/" });
    this.props.functions.changeRightImage(null);

    this.playMedia = this.playMedia.bind(this);
    this.play_torrent = this.play_torrent.bind(this);
    this.play_trailer = this.play_trailer.bind(this);
  }

  componentDidMount() {
    axios.get(window.vars.apiBase + 'movie?id=' + this.props.match.params.id).then(data => {
        console.log(data.data);
        this.props.functions.changeTitle(data.data.title);
        this.setState({movie: data.data, loading: false});
    }, err =>{
        console.log(err);
        this.setState({loading: false});
    });
  }

  play_torrent(torrent, start_from){
    this.viewRef.current.play({type: "torrent", url: torrent.url, title: this.state.movie.title, played_for: start_from, length: this.state.movie.length});
  }

  play_trailer(url){
      this.viewRef.current.play({type: "trailer", url: url, title: this.state.movie.title + " Trailer"});
  }

  playMedia(instance, media)
  {
    this.setState({loading: true});
    if(media.type === "trailer"){
        axios.post(window.vars.apiBase + 'play/url?instance=' + instance
            + "&url=" + encodeURIComponent(media.url)
            + "&title=" + encodeURIComponent(this.state.movie.title + " Trailer"))
            .then(
                () => this.setState({loading: false}),
                () => this.setState({loading: false})
            );
    }else{
        if(media.played_for > 0)
            console.log("Continue from " + media.played_for);

        axios.post(window.vars.apiBase + 'play/movie?instance=' + instance
            + "&url=" + encodeURIComponent(media.url)
            + "&id=" + this.props.match.params.id
            + "&title=" + encodeURIComponent(this.state.movie.title)
            + "&img=" + encodeURIComponent(this.state.movie.images.poster)
            + "&position=" + media.played_for)
            .then(
                () => this.setState({loading: false}),
                () => this.setState({loading: false})
            );
    }
  }

  render() {
    const movie = this.state.movie;
    const releaseDate = new Date();
    const torrents = Object.entries(movie.torrents.en).sort((a, b) => a[0] < b[0]);
    if (movie.released)
        releaseDate.setTime(movie.released * 1000);
    const showPopup = this.state.showPopup;
    const loading = this.state.loading;

    return (
        <MediaPlayerView ref={this.viewRef} playMedia={this.playMedia}>
          <ViewLoader loading={this.state.loading}/>
          <div className="movie">
            <div className="movie-image">
                <img alt="movie-poster" src={movie.images.poster} />
            </div>
            <div className="movie-details">
                <div className="label-row">
                    <div className="label-field">Released</div>
                    <div className="label-value">{formatTime(releaseDate, true, true, true)}</div>
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
            <div className="play-buttons">
                <Button text="Play trailer" onClick={(e) => this.play_trailer(movie.trailer)} classId="secondary"/>
                 { movie.played_for > 1000 * 60 && <Button text={"Continue from " + writeTimespan(movie.played_for)} onClick={(e) => this.play_torrent(torrents[0][1], movie.played_for)} classId="secondary"></Button> }
                { torrents.map(([res, torrent]) => <Button key={res} text={"Play " + res } onClick={(e) => this.play_torrent(torrent, 0)} classId="secondary" />)}
                <Link to={"/mediaplayer/torrents?term=" + encodeURIComponent(movie.title)}><Button text="Search torrents" onClick={(e) => {}} classId="secondary"></Button></Link>
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