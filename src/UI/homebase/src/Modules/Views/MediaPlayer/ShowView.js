import React, { Component } from 'react';
import axios from 'axios'

import View from './../View.js'
import MediaPlayerView from './MediaPlayerView.js'
import Button from './../../Components/Button'
import SelectInstancePopup from './../../Components/Popups/SelectInstancePopup'
import Popup from './../../Components/Popups/Popup'

class ShowView extends Component {
  constructor(props) {
    super(props);
    this.viewRef = React.createRef();

    this.state = {show: {images:[], rating:{}, seasons:[]}, selectedSeason: -1, selectedEpisode: -1};
    this.props.changeBack({to: "/mediaplayer/shows/" });

    this.play = this.play.bind(this);
    this.playShow = this.playShow.bind(this);
  }

  componentDidMount() {
    axios.get('http://localhost/shows/get_show?id=' + this.props.match.params.id).then(data => {
        this.viewRef.current.changeState(1);
        console.log(data.data);
        const seasonEpisodes = data.data.episodes.reduce((seasons, epi) => {
          if (!seasons[epi.season])
            seasons[epi.season] = [];
          seasons[epi.season].push(epi);
          return seasons;
        }, {});
        data.data.seasons = seasonEpisodes;
        this.setState({show: data.data});
        this.props.changeTitle(data.data.title);
    }, err =>{
        this.viewRef.current.changeState(1);
        console.log(err);
    });
  }

  seasonSelect(evnt, season){
    this.setState({selectedSeason: season});
  }

  episodeSelect(evnt, episode){
    this.setState({selectedEpisode: episode.episode});
  }

  play(episode){
    this.viewRef.current.play({url: episode.torrents["0"].url, episode: episode.episode, season: episode.season, title: this.state.show.title + " [S" + episode.season + "E" + episode.episode + "]"});
  }

  playShow(instance, episode)
  {
    this.viewRef.current.changeState(0);
    axios.post('http://localhost/play/episode?instance=' + instance
        + "&url=" + encodeURIComponent(episode.url)
        + "&id=" + this.state.show.id
        + "&title=" + encodeURIComponent(episode.title)
        + "&img=" + encodeURIComponent(this.state.show.images.poster)
        + "&season=" + episode.season
        + "&episode=" + episode.episode).then(() => {
            this.viewRef.current.changeState(1);
        }, err =>{
            console.log(err);
            this.viewRef.current.changeState(1);
        });
  }

  render() {
    const show = this.state.show;
    const selectedSeason = this.state.selectedSeason;
    const selectedEpisode = this.state.selectedEpisode;

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
                    <div className="label-value">{show.rating.percentage}%</div>
                </div>
            </div>
            <div className="show-synopsis">
                {show.synopsis}
            </div>
            <div className="show-episode-selection">
                <div className="show-seasons">
                    { Object.entries(show.seasons).map(([season, episodes]) =>
                        <div key={season} className={"show-season " + (this.state.selectedSeason == season ? 'selected' : '')} onClick={(e) => this.seasonSelect(e, season)}>Season {season}</div>
                    )}
                </div>
                {selectedSeason != -1 &&
                    <div className="show-episodes">
                        { show.seasons[selectedSeason].map((episode, index) => (
                            <div key={index} className={"show-episode " + (this.state.selectedEpisode == episode.episode ? 'selected' : '')} onClick={(e) => this.episodeSelect(e, episode)}>
                                <div className="show-episode-title truncate">{episode.episode} - {episode.title}</div>
                                { selectedEpisode == episode.episode &&
                                    <div className="show-episode-selected">
                                        <div className="show-episode-synopsis">
                                            {episode.overview}
                                        </div>
                                        <div className="show-episode-play">
                                             <Button text="Play" onClick={(e) => this.play(episode)} classId="secondary"></Button>
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