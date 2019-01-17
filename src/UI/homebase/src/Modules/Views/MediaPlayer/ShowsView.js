import React, { Component } from 'react';
import axios from 'axios'

import MediaOverview from './../../MediaList/MediaOverview.js'
import View from './../View.js'
import Popup from './../../Components/Popups/Popup.js'

class ShowsView extends Component {
  constructor(props) {
    super(props);
    this.orderOptions = [
        "Trending",
        "Name",
        "Rating",
        "Updated",
        "Year",
    ];
    this.state = {shows: [], loading: true, order: this.orderOptions[0], searchTerm: "", page: 1, maxPageReached: false};

    this.props.functions.changeBack({to: "/mediaplayer/" });
    this.props.functions.changeTitle("Shows");
    this.props.functions.changeRightImage(null);

    this.getShows = this.getShows.bind(this);
    this.changeSearchTerm = this.changeSearchTerm.bind(this);
    this.changeOrder = this.changeOrder.bind(this);
    this.changePage = this.changePage.bind(this);
  }

  componentDidMount() {
    this.getShows(1, this.state.order, "");
  }

  componentWillUnmount(){
    if (this.timer)
        clearTimeout(this.timer);
  }

  getShows(page, order, searchTerm){
    this.setState({loading: true});
    axios.get('http://'+window.location.hostname+'/shows/get_shows?page='+page+'&orderby='+encodeURIComponent(order)+'&keywords='+encodeURIComponent(searchTerm)).then(data => {
        var newShows = this.state.shows;
        for(var i = 0; i < data.data.length; i++){
            if(newShows.some(e => e.id === data.data[i].id))
                continue;
            newShows.push(data.data[i]);
        }
        this.setState({shows: newShows, loading: false, maxPageReached: data.data.length != 50});
        console.log(data.data);
    }, err =>{
        this.setState({loading: false});
        console.log(err);
    });
  }

  changeSearchTerm(term){
    this.setState({searchTerm: term, page: 1});
    if (this.timer)
        clearTimeout(this.timer);
    this.timer = setTimeout(() => {
        this.setState({shows: []});
        this.getShows(this.state.page, this.state.order, this.state.searchTerm);
    }, 750);
  }

  changeOrder(order){
    this.setState({order: order, shows: [], page: 1});
    this.getShows(1, order, this.state.searchTerm);
  }

  changePage(){
    if(this.state.maxPageReached)
        return;

    var newPage = this.state.page + 1;
    this.setState({page: newPage});
    this.getShows(newPage, this.state.order, this.state.searchTerm);
  }

  render() {
    const shows = this.state.shows;
    const loading = this.state.loading;

    return (
        <div className="media-view-wrapper">
            <MediaOverview media={shows}
                link="/mediaplayer/shows/"
                searchTerm={this.state.searchTerm}
                order={this.state.order}
                onSearchTermChange={this.changeSearchTerm}
                onChangeOrder={this.changeOrder}
                onScrollBottom={this.changePage}
                orderOptions={this.orderOptions}/>
            { loading &&
                <Popup loading={loading} />
            }
        </div>
    );
  }
};

export default ShowsView;