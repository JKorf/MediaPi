import React, { Component } from 'react';
import axios from 'axios';

import MediaPlayerView from './MediaPlayerView.js'

import SvgImage from './../../Components/SvgImage';
import Button from './../../Components/Button';
import SearchBox from './../../Components/SearchBox';
import ViewLoader from './../../Components/ViewLoader';

import movieImage from './../../../Images/movie.svg';
import showImage from './../../../Images/show.svg';
import otherImage from './../../../Images/other.svg';
import leechersImage from './../../../Images/leechers.png';
import seedersImage from './../../../Images/seeders.png';

import {updateTorrentsSearch, getTorrentsSearch} from './../../../Utils/SearchHistory.js'

class TorrentView extends Component {
  constructor(props) {
    super(props);
    this.viewRef = React.createRef();
    var prevSearch = getTorrentsSearch();
    this.state = {selectedTorrent: null, searchTerm: prevSearch.term, loading: true};

    this.selectedTorrent = null;
    this.props.functions.changeBack({ to: "/mediaplayer/" });
    this.props.functions.changeTitle("Torrents");
    this.props.functions.changeRightImage(null);

    this.playTorrent = this.playTorrent.bind(this);
    this.torrentPlay = this.torrentPlay.bind(this);
    this.searchTermChange = this.searchTermChange.bind(this);
    this.getTorrents = this.getTorrents.bind(this);
  }

  componentDidMount() {
    this.getTorrents();
  }

  componentWillUnmount(){
    if (this.timer)
        clearTimeout(this.timer);
    updateTorrentsSearch(this.state.searchTerm);
  }

  torrentPlay(torrent)
  {
      this.viewRef.current.play(torrent);
  }

  torrentSelected(torrent){
      this.setState({selectedTorrent: torrent});
  }

  searchTermChange(value){
    this.setState({searchTerm: value});
    if (this.timer)
        clearTimeout(this.timer);
    this.timer = setTimeout(() => {
        this.getTorrents();
    }, 750);
  }

  getTorrents()
  {
    this.setState({loading: true});
    if(this.state.searchTerm){

        axios.get(window.vars.apiBase + 'torrents?keywords=' + encodeURIComponent(this.state.searchTerm)).then(data => {
                console.log(data.data);
                this.setState({torrents: data.data, loading: false});
            }, err =>{
                console.log(err);
                this.setState({loading: false});
            });
    }
    else{
        axios.get(window.vars.apiBase + 'torrents/top').then(data => {
                console.log(data.data);
                this.setState({torrents: data.data, loading: false});
            }, err =>{
                console.log(err);
                this.setState({loading: false});
            });
    }
  }

  getTorrentIcon(torrent){
    if(torrent.category === "movie")
        return movieImage;
    if(torrent.category === "show")
        return showImage;
    return otherImage;
  }

  playTorrent(instance, torrent)
  {
    this.setState({loading: true});
    axios.post(window.vars.apiBase + 'play/torrent?instance=' + instance
    + "&title=" + encodeURIComponent(torrent.title)
    + "&url=" + encodeURIComponent(torrent.url)).then(
        () => this.setState({loading: false}),
        () => this.setState({loading: false})
        );
  }

  render() {
    const torrents = this.state.torrents;
    const selectedTorrent = this.state.selectedTorrent;
    return (
        <MediaPlayerView ref={this.viewRef} playMedia={this.playTorrent}>
          <ViewLoader loading={this.state.loading}/>
              { this.state.torrents &&
              <div className="torrents-wrapper">
                  <div className="torrent-search">
                        <div className="torrent-search-input"><SearchBox searchTerm={this.state.searchTerm} onChange={this.searchTermChange}/></div>
                    </div>
                  <div className="torrents">
                     { torrents.map((torrent, index) => (
                        <div className={"torrent " + (selectedTorrent === torrent ? "selected" : "")} key={index} onClick={(e) => this.torrentSelected(torrent, e)}>
                            <SvgImage src={this.getTorrentIcon(torrent)} />
                            <div className="torrent-title truncate2">{torrent.title}</div>
                            { selectedTorrent === torrent &&
                                <div className="torrent-details">
                                    <div className="torrent-details-peers">
                                        <div className="torrent-details-seeders truncate">{selectedTorrent.seeders}<img alt="Seeders" src={seedersImage} /></div>
                                        <div className="torrent-details-leechers truncate">{selectedTorrent.leechers}<img alt="Leechers" src={leechersImage} /></div>
                                    </div>
                                    <div className="torrent-details-size">{selectedTorrent.size}</div>
                                    <Button text="Play" onClick={(e) => this.torrentPlay(torrent)} classId="secondary"/>
                                </div>
                            }
                        </div>
                        ))}
                   </div>
                </div>
              }
      </MediaPlayerView>
    );
  }
};

export default TorrentView;