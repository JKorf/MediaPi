import React, { Component } from 'react';
import axios from 'axios'

import MediaOverview from './../../MediaList/MediaOverview.js'
import ViewLoader from './../../Components/ViewLoader';

import {updateShowsSearch, getShowsSearch} from './../../../Utils/SearchHistory.js'

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

    var prevSearch = getShowsSearch();
    this.state = {shows: [], loading: true, order: prevSearch.order, searchTerm: prevSearch.term, page: prevSearch.page, maxPageReached: false};

    this.props.functions.changeBack({to: "/mediaplayer/" });
    this.props.functions.changeTitle("Shows");
    this.props.functions.changeRightImage(null);

    this.getShows = this.getShows.bind(this);
    this.changeSearchTerm = this.changeSearchTerm.bind(this);
    this.changeOrder = this.changeOrder.bind(this);
    this.changePage = this.changePage.bind(this);
  }

  componentDidMount() {
    this.getShows(this.state.page, this.state.order, this.state.searchTerm, true);
  }

  componentWillUnmount(){
    if (this.timer)
        clearTimeout(this.timer);
    updateShowsSearch(this.state.searchTerm, this.state.page, this.state.order);
  }

  getShows(page, order, searchTerm, include_previous_pages){
    this.setState({loading: true});
    axios.get(window.vars.apiBase + 'shows/get_shows?page='+page+'&orderby='+encodeURIComponent(order)+'&keywords='+encodeURIComponent(searchTerm)+ "&include_previous="+include_previous_pages).then(data => {
        var newShows = this.state.shows;
        for(var i = 0; i < data.data.length; i++){
            if(newShows.some(e => e.id === data.data[i].id))
                continue;
            newShows.push(data.data[i]);
        }
        this.setState({shows: newShows, loading: false, maxPageReached: data.data.length !== 50});
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
    return (
        <div className="media-view-wrapper">
            <ViewLoader loading={this.state.loading}/>
            { this.state.shows &&
                <MediaOverview media={this.state.shows}
                    link="/mediaplayer/shows/"
                    searchTerm={this.state.searchTerm}
                    order={this.state.order}
                    onSearchTermChange={this.changeSearchTerm}
                    onChangeOrder={this.changeOrder}
                    onScrollBottom={this.changePage}
                    orderOptions={this.orderOptions}/>
            }
        </div>
    );
  }
};

export default ShowsView;