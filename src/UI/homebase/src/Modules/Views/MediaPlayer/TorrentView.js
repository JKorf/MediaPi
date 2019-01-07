import React, { Component } from 'react';
import axios from 'axios';

import View from './../View.js';
import MediaPlayerView from './MediaPlayerView.js'

import SvgImage from './../../Components/SvgImage';
import Button from './../../Components/Button';
import SelectInstancePopup from './../../Components/Popups/SelectInstancePopup.js';
import Popup from './../../Components/Popups/Popup.js';

import movieImage from './../../../Images/movie.svg';
import showImage from './../../../Images/show.svg';
import otherImage from './../../../Images/other.svg';
import leechersImage from './../../../Images/leechers.png';
import seedersImage from './../../../Images/seeders.png';


class TorrentView extends Component {
  constructor(props) {
    super(props);
    this.viewRef = React.createRef();
    this.state = {torrents: [], selectedTorrent: null};

    this.selectedTorrent = null;
    this.props.changeBack({ to: "/mediaplayer/" });

    this.playTorrent = this.playTorrent.bind(this);
    this.torrentPlay = this.torrentPlay.bind(this);
  }

  componentDidMount() {
    axios.get('http://localhost/torrent/top').then(data => {
            console.log(data.data);
            this.setState({torrents: data.data});
            this.viewRef.current.changeState(1);
        }, err =>{
            console.log(err);
            this.viewRef.current.changeState(1);
        });
  }

  torrentPlay(torrent)
  {
      this.viewRef.current.play(torrent);
  }

  torrentSelected(torrent){
      this.setState({selectedTorrent: torrent});
  }

  getTorrentIcon(torrent){
    if(torrent.category == "movie")
        return movieImage;
    if(torrent.category == "show")
        return showImage;
    return otherImage;
  }

  playTorrent(instance, torrent)
  {
    this.viewRef.current.changeState(0);
    axios.post('http://localhost/play/torrent?instance=' + instance
    + "&title=" + encodeURIComponent(torrent.title)
    + "&url=" + encodeURIComponent(torrent.url)).then(() => {
            this.viewRef.current.changeState(1);
        }, err =>{
            console.log(err);
            this.viewRef.current.changeState(1);
        });
  }

  render() {
    const torrents = this.state.torrents;
    const selectedTorrent = this.state.selectedTorrent;
    return (
        <MediaPlayerView ref={this.viewRef} playMedia={this.playTorrent}>
          <div className="torrents">
             { torrents.map((torrent, index) => (
                <div className="torrent" key={index} onClick={(e) => this.torrentSelected(torrent, e)}>
                    <SvgImage src={this.getTorrentIcon(torrent)} />
                    <div className="torrent-title truncate2">{torrent.title}</div>
                    { selectedTorrent == torrent &&
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