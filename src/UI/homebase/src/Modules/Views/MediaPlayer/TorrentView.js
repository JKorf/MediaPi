import React, { Component } from 'react';
import axios from 'axios';

import MediaPlayerView from './MediaPlayerView.js'

import SvgImage from './../../Components/SvgImage';
import Button from './../../Components/Button';
import SearchBox from './../../Components/SearchBox';

import movieImage from './../../../Images/movie.svg';
import showImage from './../../../Images/show.svg';
import otherImage from './../../../Images/other.svg';
import leechersImage from './../../../Images/leechers.png';
import seedersImage from './../../../Images/seeders.png';


class TorrentView extends Component {
  constructor(props) {
    super(props);
    this.viewRef = React.createRef();
    this.state = {torrents: [], selectedTorrent: null, searchTerm: ""};

    this.selectedTorrent = null;
    this.props.functions.changeBack({ to: "/mediaplayer/" });
    this.props.functions.changeTitle("Torrents");
    this.props.functions.changeRightImage(null);

    this.playTorrent = this.playTorrent.bind(this);
    this.torrentPlay = this.torrentPlay.bind(this);
    this.searchTermChange = this.searchTermChange.bind(this);
  }

  componentDidMount() {
    axios.get('http://'+window.location.hostname+'/torrent/top').then(data => {
            console.log(data.data);
            this.setState({torrents: data.data});
            if(this.viewRef.current) { this.viewRef.current.changeState(1); }
        }, err =>{
            console.log(err);
            if(this.viewRef.current) { this.viewRef.current.changeState(1); }
        });
  }

  componentWillUnmount(){
    if (this.timer)
        clearTimeout(this.timer);
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
        this.setState({torrents: []});
        this.viewRef.current.changeState(0);
        axios.get('http://'+window.location.hostname+'/torrent/search?keywords=' + encodeURIComponent(value)).then(data => {
                console.log(data.data);
                this.setState({torrents: data.data});
                if(this.viewRef.current) { this.viewRef.current.changeState(1); }
            }, err =>{
                console.log(err);
                if(this.viewRef.current) { this.viewRef.current.changeState(1); }
            });
    }, 750);
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
    this.viewRef.current.changeState(0);
    axios.post('http://'+window.location.hostname+'/play/torrent?instance=' + instance
    + "&title=" + encodeURIComponent(torrent.title)
    + "&url=" + encodeURIComponent(torrent.url)).then(() => {
            if(this.viewRef.current) { this.viewRef.current.changeState(1); }
            this.props.functions.showInfo(6000, "success", "Successfully started", torrent.title + " is now playing", "more..", "/mediaplayer/player/" + instance);
        }, err =>{
            console.log(err);
            if(this.viewRef.current) { this.viewRef.current.changeState(1); }
        });
  }

  render() {
    const torrents = this.state.torrents;
    const selectedTorrent = this.state.selectedTorrent;
    return (
        <MediaPlayerView ref={this.viewRef} playMedia={this.playTorrent}>
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
                                <div className="torrent-details-seeders truncate">{selectedTorrent.seeders}<img src={seedersImage} /></div>
                                <div className="torrent-details-leechers truncate">{selectedTorrent.leechers}<img src={leechersImage} /></div>
                            </div>
                            <div className="torrent-details-size">{selectedTorrent.size}</div>
                            <Button text="Play" onClick={(e) => this.torrentPlay(torrent)} classId="secondary"/>
                        </div>
                    }
                </div>
                ))}
          </div>
      </MediaPlayerView>
    );
  }
};

export default TorrentView;