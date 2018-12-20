import React, { Component } from 'react';
import axios from 'axios'

import MediaOverview from './../../../MediaList/MediaOverview'
import View from './../../View'

class ShowsView extends Component {
  constructor(props) {
    super(props);
    this.state = {shows: []};
    this.props.changeBack({to: "/mediaplayer/" });
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
        <MediaOverview media={shows} link="/mediaplayer/shows/" />
    );
  }
};

export default ShowsView;