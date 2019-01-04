import React, { Component } from 'react';
import axios from 'axios'

import View from './../View.js'
import Button from './../../Components/Button'
import SelectInstancePopup from './../../Components/Popups/SelectInstancePopup'
import Popup from './../../Components/Popups/Popup'

class ShowView extends Component {
  constructor(props) {
    super(props);
    this.state = {show: {images:[], rating:{}, seasons:[]}, selectedSeason: -1, selectedEpisode: -1, showPopup: false, loading: true};
    this.props.changeBack({to: "/mediaplayer/shows/" });

    this.instanceSelectCancel = this.instanceSelectCancel.bind(this);
    this.instanceSelect = this.instanceSelect.bind(this);
  }

  componentDidMount() {
    axios.get('http://localhost/shows/get_show?id=' + this.props.match.params.id).then(data => {
        console.log(data.data);
        const seasonEpisodes = data.data.episodes.reduce((seasons, epi) => {
          if (!seasons[epi.season])
            seasons[epi.season] = [];
          seasons[epi.season].push(epi);
          return seasons;
        }, {});
        data.data.seasons = seasonEpisodes;
        this.setState({show: data.data, loading: false});
    }, err =>{
        console.log(err);
        this.setSTate({loading: false});
    });
  }

  seasonSelect(evnt, season){
    this.setState({selectedSeason: season});
  }

  episodeSelect(evnt, episode){
    this.setState({selectedEpisode: episode.episode});
  }

  play(episode){
    this.selected = episode;
    this.setState({showPopup: true});
  }

  instanceSelectCancel()
  {
    this.setState({showPopup: false});
  }

  instanceSelect(instance)
  {
    this.setState({showPopup: false, loading: true});
    axios.post('http://localhost/play/episode?instance=' + instance
        + "&url=" + encodeURIComponent(this.selected.torrents["0"].url)
        + "&id=" + this.state.show.id
        + "&title=" + encodeURIComponent(this.state.show.title + " [S" + this.selected.season + "E" + this.selected.episode + "]")
        + "&img=" + encodeURIComponent(this.state.show.images.poster)
        + "&season=" + this.selected.season
        + "&episode=" + this.selected.episode).then(() => {
            this.setState({loading: false});
        }, err =>{
            console.log(err);
            this.setState({loading: false});
        });
  }

  render() {
    const show = this.state.show;
    const selectedSeason = this.state.selectedSeason;
    const selectedEpisode = this.state.selectedEpisode;
    const showPopup = this.state.showPopup;
    const loading = this.state.loading;

    return (
      <div className="show">
        <div className="show-image">
            <img src={show.images.poster} />
        </div>
        <div className="show-details">
            <div className="show-title">{show.title}</div>
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

export default ShowView;