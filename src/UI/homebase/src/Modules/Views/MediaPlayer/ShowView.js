import React, { Component } from 'react';
import axios from 'axios';

import MediaPlayerView from './MediaPlayerView.js';
import Button from './../../Components/Button';
import SvgImage from './../../Components/SvgImage';
import ColorIndicator from './../../Components/ColorIndicator';

import favoriteImage from './../../../Images/favorite.svg';
import favoriteFullImage from './../../../Images/favorite-full.svg';
import seenImage from './../../../Images/watched.svg';

class ShowView extends Component {
  constructor(props) {
    super(props);
    this.viewRef = React.createRef();

    this.state = {show: {images:[], rating:{}, seasons:[]}, selectedSeason: -1, selectedEpisode: -1};
    this.props.functions.changeBack({to: "/mediaplayer/shows/" });
    this.props.functions.changeRightImage({image: favoriteImage, click: this.toggleFavorite});

    this.play = this.play.bind(this);
    this.playShow = this.playShow.bind(this);
    this.toggleFavorite = this.toggleFavorite.bind(this);
  }

  componentDidMount() {
    axios.get(window.vars.apiBase + 'shows/get_show?id=' + this.props.match.params.id).then(data => {
        if(this.viewRef.current) { this.viewRef.current.changeState(0); }
        console.log(data.data);
        const seasonEpisodes = data.data.episodes.reduce((seasons, epi) => {
          if (!seasons[epi.season])
            seasons[epi.season] = [];
          seasons[epi.season].push(epi);
          return seasons;
        }, {});
        data.data.seasons = seasonEpisodes;
        this.setState({show: data.data});
        this.props.functions.changeTitle(data.data.title);
        this.props.functions.changeRightImage({image: (data.data.favorite? favoriteFullImage: favoriteImage), click: this.toggleFavorite});
    }, err => {
        if(this.viewRef.current) { this.viewRef.current.changeState(0); }
        console.log(err);
    });
  }

  seasonSelect(evnt, season){
    this.setState({selectedSeason: season});
  }

  episodeSelect(evnt, episode){
    this.setState({selectedEpisode: episode.episode});
  }

  toggleFavorite(){
    var show = this.state.show;
    show.favorite = !show.favorite;
    this.setState({show: show});
    this.props.functions.changeRightImage({image: (show.favorite? favoriteFullImage: favoriteImage), click: this.toggleFavorite});

    if(show.favorite)
        axios.post(window.vars.apiBase + 'shows/add_favorite?id=' + this.props.match.params.id + "&title=" + encodeURIComponent(show.title) + "&image=" + encodeURIComponent(show.images.poster));
    else
        axios.post(window.vars.apiBase + 'shows/remove_favorite?id=' + this.props.match.params.id);
  }

  addLeadingZero(value)
  {
    if (value > 10)
        return value;
    return "0" + value;
  }

  play(episode, played_for){
    this.viewRef.current.play({
        url: episode.torrents["0"].url,
        episode: episode.episode,
        season: episode.season,
        played_for: played_for,
        length: episode.length,
        title: this.state.show.title + " [S" + this.addLeadingZero(episode.season) + "E" + this.addLeadingZero(episode.episode) + "]"});
  }

  playShow(instance, episode)
  {
    if(episode.played_for !== 0)
        console.log("Continue from " + episode.played_for);

    axios.post(window.vars.apiBase + 'play/episode?instance=' + instance
        + "&url=" + encodeURIComponent(episode.url)
        + "&id=" + this.props.match.params.id
        + "&title=" + encodeURIComponent(episode.title)
        + "&img=" + encodeURIComponent(this.state.show.images.poster)
        + "&season=" + episode.season
        + "&episode=" + episode.episode
        + "&position=" + episode.played_for).then(() =>
            {
                if(this.viewRef.current) { this.viewRef.current.changeState(0); }
            }
        , err => {
            console.log(err);
            if(this.viewRef.current) { this.viewRef.current.changeState(0); } }
        );
  }

  writeTimespan(duration)
  {
     duration = Math.round(duration);
     var milliseconds = parseInt((duration % 1000) / 100),
      seconds = parseInt((duration / 1000) % 60),
      minutes = parseInt((duration / (1000 * 60)) % 60),
      hours = parseInt((duration / (1000 * 60 * 60)) % 24);

      hours = (hours < 10) ? "0" + hours : hours;
      minutes = (minutes < 10) ? "0" + minutes : minutes;
      seconds = (seconds < 10) ? "0" + seconds : seconds;

      if (hours > 0)
        return hours + ":" + minutes + ":" + seconds;
      return minutes + ":" + seconds;
  }

  render() {
    const show = this.state.show;
    const selectedSeason = this.state.selectedSeason;
    const selectedEpisode = this.state.selectedEpisode;
    const favorited = this.state.show.favorite;

    return (
        <MediaPlayerView ref={this.viewRef} playMedia={this.playShow}>
          <div className="show">
            <div className="show-image">
                <img src={show.images.poster} />
            </div>
            <div className="show-details">
                <div className="label-row">
                    <div className="label-field">Airs</div>
                    <div className="label-value">{show.air_day} - {show.air_time}</div>
                </div>
                <div className="label-row">
                    <div className="label-field">Seasons</div>
                    <div className="label-value">{show.num_seasons}</div>
                </div>
                <div className="label-row">
                    <div className="label-field">Length</div>
                    <div className="label-value">{show.runtime} minutes</div>
                </div>
                <div className="label-row">
                    <div className="label-field">Rating</div>
                    <div className="label-value"><ColorIndicator value={show.rating.percentage}>{show.rating.percentage}%</ColorIndicator></div>
                </div>
            </div>
            <div className="show-synopsis">
                {show.synopsis}
            </div>
            <div className="show-episode-selection">
                <div className="show-seasons">
                    { Object.entries(show.seasons).map(([season, episodes]) =>
                        <div key={season} className={"show-season " + (this.state.selectedSeason === season ? 'selected' : '')} onClick={(e) => this.seasonSelect(e, season)}>
                            <div className="show-season-title">Season {season}</div>
                            <div className="show-season-episodes">{episodes.length} episodes</div>
                        </div>
                    )}
                </div>
                {selectedSeason !== -1 &&
                    <div className="show-episodes">
                        { show.seasons[selectedSeason].map((episode, index) => (
                            <div key={index} className={"show-episode " + (this.state.selectedEpisode === episode.episode ? 'selected' : '')} onClick={(e) => this.episodeSelect(e, episode)}>
                                <div className="show-episode-title">
                                    <div className={"show-episode-title-text truncate " + (episode.seen ? "seen": "")}>{episode.episode} - {episode.title}</div>
                                    <div className="show-episode-title-date">{new Intl.DateTimeFormat('en-GB', { year: 'numeric', month: 'short', day: '2-digit' }).format(new Date(1970, 0, 0).setSeconds(episode.first_aired))}</div>
                                    { episode.seen && <div className="show-episode-title-seen"><SvgImage src={seenImage} /></div> }
                                </div>
                                { selectedEpisode == episode.episode &&
                                    <div className="show-episode-selected">
                                        <div className="show-episode-synopsis">
                                            {episode.overview}
                                        </div>
                                        <div className="show-episode-play">
                                             <Button text="Play" onClick={(e) => this.play(episode, 0)} classId="secondary"></Button>
                                             { episode.played_for > 1000 * 60 && <Button text={"Continue from " + this.writeTimespan(episode.played_for)} onClick={(e) => this.play(episode, episode.played_for)} classId="secondary"></Button> }
                                        </div>
                                    </div>
                                }
                            </div>
                        )) }
                    </div>
                }
            </div>
          </div>
      </MediaPlayerView>
    );
  }
};

export default ShowView;