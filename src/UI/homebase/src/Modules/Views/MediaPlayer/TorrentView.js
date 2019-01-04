import React, { Component } from 'react';
import axios from 'axios';

import View from './../View.js';
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
    this.state = {showPopup: false, torrents: [], selectedTorrent: null, loading: true};

    this.selectedTorrent = null;
    this.props.changeBack({ to: "/mediaplayer/" });

    this.instanceSelectCancel = this.instanceSelectCancel.bind(this);
    this.instanceSelect = this.instanceSelect.bind(this);
  }

  componentDidMount() {
    axios.get('http://localhost/torrent/top').then(data => {
            console.log(data.data);
            this.setState({torrents: data.data, loading: false});
        }, err =>{
            console.log(err);
            this.setState({loading: false});
        });
  }

  torrentClick(torrent)
  {
      this.setState({selectedTorrent: torrent});
  }

  playTorrent(torrent)
  {
      this.setState({showPopup: true});
  }

  getTorrentIcon(torrent){
    if(torrent.category == "movie")
        return movieImage;
    if(torrent.category == "show")
        return showImage;
    return otherImage;
  }

  instanceSelectCancel()
  {
    this.setState({showPopup: false});
  }

  instanceSelect(instance)
  {
    this.setState({showPopup: false, loading: true});
    axios.post('http://localhost/play/torrent?instance=' + instance
    + "&title=" + encodeURIComponent(this.state.selectedTorrent.title)
    + "&url=" + encodeURIComponent(this.state.selectedTorrent.url)).then(() => {
            this.setState({loading: false});
        }, err =>{
            console.log(err);
            this.setState({loading: false});
        });
  }

  render() {
    const torrents = this.state.torrents;
    const showPopup = this.state.showPopup;
    const selectedTorrent = this.state.selectedTorrent;
    const loading = this.state.loading;
    return (
      <div className="torrents">
         { torrents.map((torrent, index) => (
            <div className="torrent" key={index} onClick={(e) => this.torrentClick(torrent, e)}>
                <SvgImage src={this.getTorrentIcon(torrent)} />
                <div className="torrent-title truncate2">{torrent.title}</div>
                { selectedTorrent == torrent &&
                    <div className="torrent-details">
                        <div className="torrent-details-peers">
                            <div className="torrent-details-seeders truncate">{selectedTorrent.seeders}<img src={seedersImage} /></div>
                            <div className="torrent-details-leechers truncate">{selectedTorrent.leechers}<img src={leechersImage} /></div>
                        </div>
                        <div className="torrent-details-size">{selectedTorrent.size}</div>
                        <Button text="Play" onClick={(e) => this.playTorrent(torrent)} classId="secondary"/>
                    </div>
                }
            </div>
            ))}
            { showPopup &&
                <SelectInstancePopup onCancel={this.instanceSelectCancel} onSelect={this.instanceSelect} />
            }
            { loading &&
              <Popup loading={true} />
            }
      </div>
    );
  }
};

export default TorrentView;