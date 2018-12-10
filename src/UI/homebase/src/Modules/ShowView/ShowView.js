import React, { Component } from 'react';
import axios from 'axios'
import MediaThumbnail from './../MediaThumbnail'
import Button from './../Components/Button'

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

  btnClick() {
    axios.post('http://localhost/hd/play_file?filename=jellies.mp4&path=C:/jellies.mp4');
  }

  render() {
    const shows = this.state.shows;
    return (
      <div className="show-view">
        <Button text="Test" onClick={this.btnClick} />
      {
        shows.map((show) => <MediaThumbnail key={show._id} img={show.images.poster} title={show.title} />)
      }
      </div>
    );
  }
};

export default ShowView;