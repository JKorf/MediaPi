import React, { Component } from 'react';
import axios from 'axios'

import MediaOverview from './../../../MediaList/MediaOverview'
import View from './../../View'

class ShowsView extends Component {
  constructor(props) {
    super(props);
    this.state = {shows: []};
  }

  componentDidMount() {
    axios.get('http://localhost/shows/get_shows_all?page=1&orderby=trending&keywords=').then(data => {
        this.setState({shows: data.data})
        console.log(data.data);
    }, err =>{
        console.log(err);
    });
  }

  render() {
    const shows = this.state.shows;
    return (
      <div>
        <MediaOverview media={shows} link="/mediaplayer/shows/" />
      </div>
    );
  }
};

export default ShowsView;