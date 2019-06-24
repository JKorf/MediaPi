/*eslint no-loop-func: "off"*/

import React, { Component } from 'react';
import axios from 'axios'

import MediaOverview from './../../MediaList/MediaOverview.js'
import ViewLoader from './../../Components/ViewLoader';

import {updateYouTubeSearch, getYouTubeSearch} from './../../../Utils/SearchHistory.js'

class YouTubeMainView extends Component {
  constructor(props) {
    super(props);
    this.orderOptions = [
        "Video",
        "Channel"
    ];

    var prevSearch = getYouTubeSearch();
    this.state = {videos: [], channels: [], loading: true, order: prevSearch.order, searchTerm: prevSearch.term, page: prevSearch.page};

    this.props.functions.changeBack({to: "/mediaplayer/" });
    this.props.functions.changeTitle("YouTube");
    this.props.functions.changeRightImage(null);

    this.getData = this.getData.bind(this);
    this.changeSearchTerm = this.changeSearchTerm.bind(this);
    this.changeOrder = this.changeOrder.bind(this);
    this.changePage = this.changePage.bind(this);
  }

  componentDidMount() {
    this.getData(this.state.page, this.state.order, this.state.searchTerm, true);
  }

  componentWillUnmount(){
    if (this.timer)
        clearTimeout(this.timer);
    updateYouTubeSearch(this.state.searchTerm, this.state.page, this.state.order);
  }

  getData(page, order, searchTerm, include_previous_pages){
    this.setState({loading: true});

    if(searchTerm){
        var url = window.vars.apiBase + 'youtube/search?page='+page+'&type='+encodeURIComponent(order)+'&keywords='+encodeURIComponent(searchTerm);
        if (page !== 1 && this.state.token)
            url += "&token=" + this.state.token;

        axios.get(url).then(data => {
            console.log(data.data);

            if (order === "Video"){
                var newVideos = data.data.search_result;
                if (page !== 1){
                    newVideos = this.state.videos;
                    for(var i = 0; i < data.data.search_result.length; i++){
                        if(newVideos.some(e => e.id === data.data.search_result[i].id))
                            continue;
                        newVideos.push(data.data.search_result[i]);
                    }
                }

                this.setState({channels: [], videos: newVideos, loading: false, token: data.data.token});
            }else{
                var newChannels = data.data.search_result;
                if (page !== 1){
                    newChannels = this.state.channels;
                    for(var j = 0; j < data.data.search_result.length; j++){
                        if(newChannels.some(e => e.id === data.data.search_result[j].id))
                            continue;
                        newChannels.push(data.data.search_result[j]);
                    }
                }
                console.log(newChannels);
                this.setState({videos: [], channels: newChannels, loading: false, token: data.data.token});
            }
        }, err =>{
            this.setState({loading: false});
            console.log(err);
        });
    }
    else{
        axios.get(window.vars.apiBase + 'youtube?page='+page).then(data => {
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
  }

  changeSearchTerm(term){
    this.setState({searchTerm: term, page: 1});
    if (this.timer)
        clearTimeout(this.timer);
    this.timer = setTimeout(() => {
        this.setState({shows: []});
        this.getData(this.state.page, this.state.order, this.state.searchTerm);
    }, 750);
  }

  changeOrder(order){
    this.setState({order: order});

    if (this.state.searchTerm){
        this.setState({videos: [], page: 1});
        this.getData(1, order, this.state.searchTerm);
    }
  }

  changePage(){
    if(this.state.maxPageReached)
        return;

    var newPage = this.state.page + 1;
    this.setState({page: newPage});
    this.getData(newPage, this.state.order, this.state.searchTerm);
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
            { this.state.videos.length > 0 &&
                <MediaOverview media={this.state.videos}
                    link="/mediaplayer/youtube/v/"
                    searchTerm={this.state.searchTerm}
                    order={this.state.order}
                    onSearchTermChange={this.changeSearchTerm}
                    onChangeOrder={this.changeOrder}
                    onScrollBottom={this.changePage}
                    orderOptions={this.orderOptions}
                    getMediaItem={this.getMediaItem}
                    />
            }

            { this.state.channels.length > 0 &&
                <MediaOverview media={this.state.channels}
                    link="/mediaplayer/youtube/c/"
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