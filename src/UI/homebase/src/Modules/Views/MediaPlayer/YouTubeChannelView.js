/*eslint no-loop-func: "off"*/

import React, { Component } from 'react';
import axios from 'axios';
import { formatTime } from './../../../Utils/Util.js';

import MediaPlayerView from './MediaPlayerView.js';
import ViewLoader from './../../Components/ViewLoader/ViewLoader'
import MediaOverview from './../../MediaList/MediaOverview.js'
import favoriteImage from './../../../Images/favorite.svg';
import favoriteFullImage from './../../../Images/favorite-full.svg';

class YouTubeChannelView extends Component {
  constructor(props) {
    super(props);
    this.viewRef = React.createRef();

    this.state = {loading: true, page: 1};
    this.props.functions.changeBack({to: "/mediaplayer/youtube/" });

    this.changePage = this.changePage.bind(this);
    this.toggleFavorite = this.toggleFavorite.bind(this);
    this.getData = this.getData.bind(this);

    this.props.functions.changeRightImage({image: favoriteImage, click: this.toggleFavorite});
  }


  componentDidMount() {
    this.getData(1);
  }

  getData(page){
    var url =window.vars.apiBase + 'youtube/channel?id=' + this.props.match.params.id + "&page=" + page;
    if (page !== 1)
        url += "&token=" + this.state.channel.token;

    axios.get(url).then(data => {
        console.log(data.data);

        if (page !== 1){
            var newVideos = this.state.channel.uploads;
            for(var i = 0; i < data.data.uploads.length; i++){
                if(newVideos.some(e => e.id === data.data.uploads[i].id))
                    continue;
                newVideos.push(data.data.uploads[i]);
            }
            data.data.uploads = newVideos;
        }

        this.setState({channel: data.data, loading: false});
        this.props.functions.changeTitle(data.data.title);
        this.props.functions.changeRightImage({image: (data.data.favorite? favoriteFullImage: favoriteImage), click: this.toggleFavorite});
    }, err => {
        this.setState({ loading: false});
        console.log(err);
    });
  }

  toggleFavorite(){
    var channel = this.state.channel;
    channel.favorite = !channel.favorite;
    this.setState({channel: channel});
    this.props.functions.changeRightImage({image: (channel.favorite? favoriteFullImage: favoriteImage), click: this.toggleFavorite});

    if(channel.favorite)
        axios.post(window.vars.apiBase + 'youtube/favorite?id=' + this.props.match.params.id + "&title=" + encodeURIComponent(channel.title) + "&image=" + encodeURIComponent(channel.thumbnail));
    else
        axios.delete(window.vars.apiBase + 'youtube/favorite?id=' + this.props.match.params.id);
  }

  getMediaItem(item){
     return (
        <div className="media-thumbnail">
            <img className="media-thumbnail-img" alt="Media thumbnail" src={item.poster} />
            <div className="media-thumbnail-info">
                <div className="youtube-thumbnail-info-title truncate2">{item.title}</div>
                <div className="youtube-channel-title">{formatTime(item.upload_date, true, true, true)}</div>
            </div>
          </div>
     );
  }

  changePage(){
    if(this.state.maxPageReached)
        return;

    var newPage = this.state.page + 1;
    this.setState({page: newPage});
    this.getData(newPage);
  }

  render() {

    return (
        <MediaPlayerView ref={this.viewRef} playMedia={this.playVideo}>
          <ViewLoader loading={this.state.loading}/>
          { this.state.channel &&
              <div className="show">
                <div className="youtube-channel-image">
                    <img alt="Show poster" src={this.state.channel.thumbnail} />
                </div>
                <div className="channel-details">
                    <div className="label-row">
                        <div className="label-field">Views</div>
                        <div className="label-value">{this.state.channel.views}</div>
                    </div>
                    <div className="label-row">
                        <div className="label-field">Subs</div>
                        <div className="label-value">{this.state.channel.subs}</div>
                    </div>
                    <div className="label-row">
                        <div className="label-field">Videos</div>
                        <div className="label-value">{this.state.channel.videos}</div>
                    </div>
                </div>

                <div className="youtube-synopsis" dangerouslySetInnerHTML={{__html: this.state.channel.description}}>
                </div>

                <div className="youtube-sub-title">Videos</div>

                { this.state.channel &&
                <MediaOverview media={this.state.channel.uploads}
                    link="/mediaplayer/youtube/v/"
                    noSearch={true}
                    onScrollBottom={this.changePage}
                    getMediaItem={this.getMediaItem}
                    />
                }
              </div>
          }
      </MediaPlayerView>
    );
  }
};

export default YouTubeChannelView;