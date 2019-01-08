import React, { Component } from 'react';
import axios from 'axios'

import MediaOverview from './../../MediaList/MediaOverview.js'
import View from './../View.js'
import Popup from './../../Components/Popups/Popup.js'

class ShowsView extends Component {
  constructor(props) {
    super(props);
    this.state = {shows: [], loading: true};
    this.props.changeBack({to: "/mediaplayer/" });
    this.props.changeTitle("Shows");
  }

  componentDidMount() {
    axios.get('http://localhost/shows/get_shows_all?page=1&orderby=trending&keywords=').then(data => {
        this.setState({shows: data.data, loading: false});
        console.log(data.data);
    }, err =>{
        this.setState({loading: false});
        console.log(err);
    });
  }

  render() {
    const shows = this.state.shows;
    const loading = this.state.loading;
    return (
        <div>
        <MediaOverview media={shows} link="/mediaplayer/shows/" />
        { loading &&
            <Popup loading={loading} />
        }
        </div>
    );
  }
};

export default ShowsView;