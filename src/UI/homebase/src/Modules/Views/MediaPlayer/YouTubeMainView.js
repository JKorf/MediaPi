import React, { Component } from 'react';
import axios from 'axios'

import MediaOverview from './../../MediaList/MediaOverview.js'
import ViewLoader from './../../Components/ViewLoader';

import {updateYouTubeSearch, getYouTubeSearch} from './../../../Utils/SearchHistory.js'

class YouTubeMainView extends Component {
  constructor(props) {
    super(props);
    this.orderOptions = [
        "Trending"
    ];

    var prevSearch = getYouTubeSearch();
    this.state = {videos: [], loading: true, order: prevSearch.order, searchTerm: prevSearch.term, page: prevSearch.page};

    this.props.functions.changeBack({to: "/mediaplayer/" });
    this.props.functions.changeTitle("YouTube");
    this.props.functions.changeRightImage(null);

    this.getVideos = this.getVideos.bind(this);
    this.changeSearchTerm = this.changeSearchTerm.bind(this);
    this.changeOrder = this.changeOrder.bind(this);
    this.changePage = this.changePage.bind(this);
  }

  componentDidMount() {
    this.getVideos(this.state.page, this.state.order, this.state.searchTerm, true);
  }

  componentWillUnmount(){
    if (this.timer)
        clearTimeout(this.timer);
    updateYouTubeSearch(this.state.searchTerm, this.state.page, this.state.order);
  }

  getVideos(page, order, searchTerm, include_previous_pages){
    this.setState({loading: true});
    axios.get(window.vars.apiBase + 'youtube?page='+page+'&orderby='+encodeURIComponent(order)+'&keywords='+encodeURIComponent(searchTerm)).then(data => {
        var newVideos = this.state.videos;
        for(var i = 0; i < data.data.length; i++){
            for(var i2 = 0; i2 < data.data[i].uploads.length; i2++){
                if(newVideos.some(e => e.id === data.data[i].uploads[i2].id))
                    continue;
                newVideos.push(data.data[i].uploads[i2]);
            }
        }

        newVideos = newVideos.sort(function(a, b) {  return b.upload_date - a.upload_date; });
        this.setState({videos: newVideos, loading: false});
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
        this.getVideos(this.state.page, this.state.order, this.state.searchTerm);
    }, 750);
  }

  changeOrder(order){
    this.setState({order: order, shows: [], page: 1});
    this.getVideos(1, order, this.state.searchTerm);
  }

  changePage(){
    if(this.state.maxPageReached)
        return;

    var newPage = this.state.page + 1;
    this.setState({page: newPage});
    this.getVideos(newPage, this.state.order, this.state.searchTerm);
  }

  getMediaItem(item){
     return (
        <div className="media-thumbnail">
            <img className="media-thumbnail-img" alt="Media thumbnail" src={item.poster} />
            <div className="media-thumbnail-info">
                <div className="youtube-thumbnail-info-title truncate2">{item.title}</div>
                <div className="youtube-channel-title">{item.channel_title}</div>
            </div>
          </div>
     );
  }

  render() {
    return (
        <div className="media-view-wrapper">
            <ViewLoader loading={this.state.loading}/>
            { this.state.videos &&
                <MediaOverview media={this.state.videos}
                    link="/mediaplayer/youtube/"
                    searchTerm={this.state.searchTerm}
                    order={this.state.order}
                    onSearchTermChange={this.changeSearchTerm}
                    onChangeOrder={this.changeOrder}
                    onScrollBottom={this.changePage}
                    orderOptions={this.orderOptions}
                    getMediaItem={this.getMediaItem}
                    />
            }
        </div>
    );
  }
};

export default YouTubeMainView;