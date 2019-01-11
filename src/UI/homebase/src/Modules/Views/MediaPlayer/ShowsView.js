import React, { Component } from 'react';
import axios from 'axios'

import MediaOverview from './../../MediaList/MediaOverview.js'
import View from './../View.js'
import Popup from './../../Components/Popups/Popup.js'

class ShowsView extends Component {
  constructor(props) {
    super(props);
    this.state = {shows: [], loading: true};
    this.props.functions.changeBack({to: "/mediaplayer/" });
    this.props.functions.changeTitle("Shows");

    this.search = this.search.bind(this);
  }

  componentDidMount() {
    this.getShows(1, "trending", "");
  }

  getShows(page, order, searchTerm){
    axios.get('http://localhost/shows/get_shows?page='+page+'&orderby='+order+'&keywords='+encodeURIComponent(searchTerm)).then(data => {
        this.setState({shows: data.data, loading: false});
        console.log(data.data);
    }, err =>{
        this.setState({loading: false});
        console.log(err);
    });
  }

  search(term){
    console.log("Search " + term);
    this.getShows(1, "trending", term);
  }

  render() {
    const shows = this.state.shows;
    const loading = this.state.loading;

    return (
        <div className="media-view-wrapper">
            <MediaOverview media={shows} link="/mediaplayer/shows/" onSearch={this.search} />
            { loading &&
                <Popup loading={loading} />
            }
        </div>
    );
  }
};

export default ShowsView;