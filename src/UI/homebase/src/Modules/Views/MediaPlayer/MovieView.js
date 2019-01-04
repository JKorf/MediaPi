import React, { Component } from 'react';
import axios from 'axios';

import View from './../View.js';
import Button from './../../Components/Button';
import SelectInstancePopup from './../../Components/Popups/SelectInstancePopup'
import Popup from './../../Components/Popups/Popup'

class MovieView extends Component {
  constructor(props) {
    super(props);
    this.state = {movie: {images:[], rating: {}, torrents: {en: {}}}, showPopup: false, loading: true};
    this.props.changeBack({to: "/mediaplayer/movies/" });

    this.instanceSelectCancel = this.instanceSelectCancel.bind(this);
    this.instanceSelect = this.instanceSelect.bind(this);
  }

  componentDidMount() {
    axios.get('http://localhost/movies/get_movie?id=' + this.props.match.params.id).then(data => {
        console.log(data.data);
        this.setState({movie: data.data, loading: false});
    }, err =>{
        console.log(err);
        this.setState({loading: false});
    });
  }

  play_torrent(torrent){
    this.selected = {type: "torrent", url: torrent.url};
    this.setState({showPopup: true});
  }

  play_trailer(url){
    this.selected = {type: "trailer", url: url};
    this.setState({showPopup: true});
  }

  instanceSelectCancel()
  {
    this.setState({showPopup: false});
  }

  instanceSelect(instance)
  {
    this.setState({showPopup: false, loading: true});
    if(this.selected.type == "trailer"){
        axios.post('http://localhost/play/url?instance=' + instance
            + "&url=" + encodeURIComponent(this.selected.url)
            + "&title=" + encodeURIComponent(this.state.movie.title + " Trailer"))
            .then(
                () => this.setState({loading: false}),
                ()=> this.setState({loading: false})
            );
    }else{
        axios.post('http://localhost/play/movie?instance=' + instance
            + "&url=" + encodeURIComponent(this.selected.url)
            + "&id=" + this.state.movie.id
            + "&title=" + encodeURIComponent(this.state.movie.title)
            + "&img=" + encodeURIComponent(this.state.movie.images.poster))
            .then(
                () => this.setState({loading: false}),
                ()=> this.setState({loading: false})
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
      <div className="movie">
        <div className="movie-image">
            <img src={movie.images.poster} />
        </div>
        <div className="movie-details">
            <div className="show-title">{movie.title}</div>
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
    );
  }
};

export default MovieView;