import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";

import SearchBox from './../Components/SearchBox/'
import MediaThumbnail from './MediaThumbnail.js'

class MediaOverview extends Component {
  constructor(props) {
    super(props);
    this.lastScrollEvent = new Date();
  }

  handleScroll = (e) => {
    if(new Date().getTime() - this.lastScrollEvent.getTime() < 1000)
        return;

    const bottom = (e.target.scrollHeight - 100) - e.target.scrollTop <= e.target.clientHeight;
    if (bottom) {
        this.lastScrollEvent = new Date();
        this.props.onScrollBottom();
    }
  }

   render() {
        return (
        <div className="media-list" onScroll={this.handleScroll}>
            <div className="media-search">
                <div className="media-search-input"><SearchBox searchTerm={this.props.searchTerm} onChange={this.props.onSearchTermChange}/></div>
                <div className="media-search-order">
                    <select onChange={(e) => this.props.onChangeOrder(e.target.value)} value={this.props.order}>
                        { this.props.orderOptions.map((option) => <option key={option} value={option}>{option}</option>) }
                    </select>
                </div>
            </div>
            <div className="media-overview">
          {
            this.props.media.map((media) =>
                <Link key={media.id} to={this.props.link + media.id}>
                    <MediaThumbnail img={media.poster} title={media.title} rating={media.rating} />
                </Link>)
          }
        </div>
    </div>)
   }
}

export default MediaOverview;