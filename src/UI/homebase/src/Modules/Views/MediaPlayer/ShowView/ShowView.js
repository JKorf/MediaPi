import React, { Component } from 'react';
import axios from 'axios'

import MediaOverview from './../../../MediaList/MediaOverview'
import View from './../../View'

class ShowView extends Component {
  constructor(props) {
    super(props);
    this.state = {show: {images:[]}};
  }

  componentDidMount() {
    axios.get('http://localhost/shows/get_show?id=' + this.props.match.params.id).then(data => {
        console.log(data.data);
        this.setState({show: data.data});
    }, err =>{
        console.log(err);
    });
  }

  render() {
    const show = this.state.show;
    return (
      <div className="show">
        <div className="show-image">
            <img src={show.images.poster} />
        </div>
        <div className="show-synopsis">
            {show.synopsis}
        </div>
        <div className="show-episodes">

        </div>
      </div>
    );
  }
};

export default ShowView;