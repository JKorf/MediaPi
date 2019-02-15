import React, { Component } from 'react';
import { Link } from "react-router-dom";
import axios from 'axios';

import Widget from './Widget.js';

class FavoriteSeriesWidget extends Component {
  constructor(props) {
    super(props);

    this.state = {};
    this.getSize = this.getSize.bind(this);
  }


  getSize(){
     return {width: 250, height: 34 + 150};
  }

  componentDidMount() {
    axios.get(window.vars.apiBase + 'data/get_favorites').then(data => {
            console.log(data.data);
            this.setState({favorites: data.data.filter(f => f.type == "Show")});
        }, err =>{
            console.log(err);
        });
  }

  componentWillUnmount(){
  }

  render() {
    var shows = this.state.favorites;

    return (
      <Widget {...this.props} loading={!this.state.favorites}>
        { this.state.favorites &&
            <div className="favorites-widget">
            { shows.map((fav) =>
                <Link to={"/mediaplayer/shows/" + fav.id} key={fav.id}>
                    <div className="favorite-item">
                        <div className="favorite-item-image"><img src={fav.image} /></div>
                    </div>
                </Link>
            )}
            </div>
        }
      </Widget>
    );
  }
};

export default FavoriteSeriesWidget;