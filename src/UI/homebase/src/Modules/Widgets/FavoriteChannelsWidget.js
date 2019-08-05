import React, { Component } from 'react';
import { Link } from "react-router-dom";
import axios from 'axios';

import Widget from './Widget.js';

class FavoriteChannelsWidget extends Component {
  constructor(props) {
    super(props);

    this.state = {favorites: []};
    this.getSize = this.getSize.bind(this);
  }

  shouldShow(){
    return this.state.favorites.length > 0;
  }

  getSize(){
     return {width: 180, height: 34 + 80};
  }

  componentDidMount() {
    axios.get(window.vars.apiBase + 'data/favorites').then(data => {
            console.log(data.data);
            this.setState({favorites: data.data.filter(f => f.type === "YouTube")});
        }, err =>{
            console.log(err);
        });
  }

  componentWillUnmount(){
  }

  render() {
    return (
      <Widget {...this.props} loading={!this.state.favorites}>
        { this.state.favorites &&
            <div className="favorites-widget">
            { this.state.favorites.length === 0 &&
                <div className="favorite-none">No favorites yet</div>
            }
            { this.state.favorites.map((fav) =>
                <Link to={"/mediaplayer/youtube/c/" + fav.id} key={fav.id}>
                    <div className="favorite-item">
                        <div className="favorite-item-image"><img alt="Favorite poster" src={fav.image} /></div>
                    </div>
                </Link>
            )}
            </div>
        }
      </Widget>
    );
  }
};

export default FavoriteChannelsWidget;