import React, { Component } from 'react';
import axios from 'axios'

import MediaOverview from './../../MediaList/MediaOverview.js'
import View from './../View.js'
import Popup from './../../Components/Popups/Popup.js'

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
    this.state = {movies: [], loading: true, order: this.orderOptions[0], searchTerm: "", page: 1, maxPageReached: false};


    this.props.functions.changeBack({to: "/mediaplayer/"});
    this.props.functions.changeTitle("Movies");
    this.props.functions.changeRightImage(null);

    this.getMovies = this.getMovies.bind(this);
    this.changeSearchTerm = this.changeSearchTerm.bind(this);
    this.changeOrder = this.changeOrder.bind(this);
    this.changePage = this.changePage.bind(this);
  }

  componentDidMount() {
    this.getMovies(1, this.state.order, "");
  }

  componentWillUnmount(){
    if (this.timer)
        clearTimeout(this.timer);
  }

  getMovies(page, order, search){
    this.setState({loading: true});
    axios.get('http://'+window.location.hostname+'/movies/get_movies?page='+page+'&orderby='+encodeURIComponent(order)+'&keywords=' + encodeURIComponent(search)).then(data => {
        var newMovies = this.state.movies;
        for(var i = 0; i < data.data.length; i++){
            if(newMovies.some(e => e.id === data.data[i].id))
                continue;
            newMovies.push(data.data[i]);
        }
        this.setState({movies: newMovies, loading: false, maxPageReached: data.data.length != 50});
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
        this.getMovies(this.state.page, this.state.order, this.state.searchTerm);
    }, 750);
  }

  changeOrder(order){
    this.setState({order: order, movies: [], page: 1});
    this.getMovies(1, order, this.state.searchTerm);
  }

   changePage(){
    if(this.state.maxPageReached)
        return;

    var newPage = this.state.page + 1;
    this.setState({page: newPage});
    this.getMovies(newPage, this.state.order, this.state.searchTerm);
  }

  render() {
    const movies = this.state.movies;
    const loading = this.state.loading;
    return (
       <div className="media-view-wrapper">
            <MediaOverview media={movies}
                link="/mediaplayer/movies/"
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

export default MoviesView;