import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";

import SearchBox from './../Components/SearchBox/'
import MediaThumbnail from './MediaThumbnail.js'

class MediaOverview extends Component {
  constructor(props) {
    super(props);
  }

   render() {
        return (
        <div className="media-list">
        <div className="media-search">
            <div className="media-search-input"><SearchBox onChange={this.props.onSearch}/></div>
            <div className="media-search-order">
                <select>
                    <option value="trending">Trending</option>
                    <option value="released">Released</option>
                </select>
            </div>
        </div>
        <div className="media-overview">
      {
        this.props.media.map((media) =>
            <Link key={media.id} to={this.props.link + media.id}>
                <MediaThumbnail img={media.poster ? media.poster: media.images.poster} title={media.title} rating={media.rating} />
            </Link>)
      }
    </div>
    </div>)
   }
}

export default MediaOverview;