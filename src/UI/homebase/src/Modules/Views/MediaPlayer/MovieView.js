import React, { Component } from 'react';
import axios from 'axios'

import View from './../View.js'

class MovieView extends Component {
  constructor(props) {
    super(props);
    this.state = {movie: {images:[]}};
    this.props.changeBack({to: "/mediaplayer/movies/" });
  }

  componentDidMount() {
  console.log(this.props)
    axios.get('http://localhost/movies/get_movie?id=' + this.props.match.params.id).then(data => {
        console.log(data.data);
        this.setState({movie: data.data});
    }, err =>{
        console.log(err);
    });
  }

  render() {
    const movie = this.state.movie;
    return (
      <div className="movie">
        <div className="movie-image">
            <img src={movie.poster} />
        </div>
        <div className="movie-synopsis">
            {movie.synopsis}
        </div>
      </div>
    );
  }
};

export default MovieView;