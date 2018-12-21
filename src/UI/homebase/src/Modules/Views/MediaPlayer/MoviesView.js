import React, { Component } from 'react';
import axios from 'axios'

import MediaOverview from './../../MediaList/MediaOverview.js'
import View from './../View.js'

class MoviesView extends Component {
  constructor(props) {
    super(props);
    this.state = {movies: []};
    this.props.changeBack({to: "/mediaplayer/"});
  }

  componentDidMount() {
    axios.get('http://localhost/movies/get_movies_all?page=1&orderby=trending&keywords=').then(data => {
        console.log(data.data);
        this.setState({movies: data.data});

    }, err =>{
        console.log(err);
    });
  }

  render() {
    const movies = this.state.movies;
    return (
        <MediaOverview media={movies} link="/mediaplayer/movies/" />
    );
  }
};

export default MoviesView;