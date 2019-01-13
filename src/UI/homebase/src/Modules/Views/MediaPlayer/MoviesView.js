import React, { Component } from 'react';
import axios from 'axios'

import MediaOverview from './../../MediaList/MediaOverview.js'
import View from './../View.js'
import Popup from './../../Components/Popups/Popup.js'

class MoviesView extends Component {
  constructor(props) {
    super(props);
    this.state = {movies: [], loading: true};
    this.props.functions.changeBack({to: "/mediaplayer/"});
    this.props.functions.changeTitle("Movies");
    this.getMovies = this.getMovies.bind(this);
    this.search = this.search.bind(this);
  }

  componentDidMount() {
    this.search(1, "trending", "");
  }

  getMovies(page, order, search){
    axios.get('http://'+window.location.hostname+'/movies/get_movies?page='+page+'&orderby='+order+'&keywords=' + encodeURIComponent(search)).then(data => {
        console.log(data.data);
        this.setState({movies: data.data, loading: false});
    }, err =>{
        console.log(err);
        this.setState({loading: false});
    });
  }

  search(term){
    console.log("Search " + term);
    this.getMovies(1, "trending", term);
  }

  render() {
    const movies = this.state.movies;
    return (
        <div className="media-view-wrapper">
            <MediaOverview media={movies} link="/mediaplayer/movies/" onSearch={this.search}/>
        { this.state.loading &&
            <Popup loading={this.state.loading} />
        }
        </div>
    );
  }
};

export default MoviesView;