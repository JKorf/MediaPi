import React, { Component } from 'react';
import axios from 'axios'
import MediaThumbnail from './../MediaThumbnail'

class ShowView extends Component {
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
      <div className="show-view">
      {
        shows.map((show) => <MediaThumbnail key={show._id} img={show.images.poster} title={show.title} />)
      }
        <MediaThumbnail img="https://cdn-images-1.medium.com/max/800/0*d42LtNfXWXB_77uc" title="Test title" />
        <MediaThumbnail img="https://cdn-images-1.medium.com/max/800/0*d42LtNfXWXB_77uc" title="Test title2" />
      </div>
    );
  }
};

export default ShowView;