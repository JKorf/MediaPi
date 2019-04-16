/*eslint no-loop-func: "off"*/

import React, { Component } from 'react';
import axios from 'axios'

import MediaOverview from './../../MediaList/MediaOverview.js'
import ViewLoader from './../../Components/ViewLoader';

import {updateMoviesSearch, getMoviesSearch} from './../../../Utils/SearchHistory.js'

class MoviesView extends Component {
  constructor(props) {
    super(props);
    this.orderOptions = [
        "Trending",
        "Last added",
        "Rating",
        "Title",
        "Year",
    ];
    var prevSearch = getMoviesSearch();
    this.state = {movies: [], loading: true, order: prevSearch.order, searchTerm: prevSearch.term, page: prevSearch.page, maxPageReached: false};

    this.props.functions.changeBack({to: "/mediaplayer/"});
    this.props.functions.changeTitle("Movies");
    this.props.functions.changeRightImage(null);

    this.getMovies = this.getMovies.bind(this);
    this.changeSearchTerm = this.changeSearchTerm.bind(this);
    this.changeOrder = this.changeOrder.bind(this);
    this.changePage = this.changePage.bind(this);
  }

  componentDidMount() {
    this.getMovies(this.state.page, this.state.order, this.state.searchTerm, true);
  }

  componentWillUnmount(){
    if (this.timer)
        clearTimeout(this.timer);
    updateMoviesSearch(this.state.searchTerm, this.state.page, this.state.order);
  }

  getMovies(page, order, search, include_previous_pages){
    this.setState({loading: true});
    axios.get(window.vars.apiBase + 'movies?page='+page+'&orderby='+encodeURIComponent(order)+'&keywords=' + encodeURIComponent(search)+ "&include_previous="+include_previous_pages).then(data => {
        var newMovies = this.state.movies;
        for(var i = 0; i < data.data.length; i++){
            if(newMovies.some(e => e.id === data.data[i].id))
                continue;
            newMovies.push(data.data[i]);
        }
        this.setState({movies: newMovies, loading: false, maxPageReached: data.data.length !== 50});
        console.log(data.data);
    }, err =>{
        console.log(err);
        this.setState({loading: false});
    });
  }

  changeSearchTerm(term){
    this.setState({searchTerm: term, page: 1});
    if (this.timer)
        clearTimeout(this.timer);
    this.timer = setTimeout(() => {
        this.setState({movies: []});
        this.getMovies(this.state.page, this.state.order, this.state.searchTerm, false);
    }, 750);
  }

  changeOrder(order){
    this.setState({order: order, movies: [], page: 1});
    this.getMovies(1, order, this.state.searchTerm, false);
  }

   changePage(){
    if(this.state.maxPageReached)
        return;

    var newPage = this.state.page + 1;
    this.setState({page: newPage});
    this.getMovies(newPage, this.state.order, this.state.searchTerm, false);
  }

  render() {
    return (
       <div className="media-view-wrapper">
           <ViewLoader loading={this.state.loading}/>
            { this.state.movies &&
                <MediaOverview media={this.state.movies}
                    link="/mediaplayer/movies/"
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

export default MoviesView;