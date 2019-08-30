import React, { Component } from 'react';
import axios from 'axios';

import MediaPlayerView from './MediaPlayerView.js'

import Button from './../../Components/Button';
import ViewLoader from './../../Components/ViewLoader';
import SearchBox from './../../Components/SearchBox';

class UrlView extends Component {
  constructor(props) {
    super(props);
    this.viewRef = React.createRef();

    this.state = {url: "", loading: false};

    this.props.functions.changeBack({ to: "/mediaplayer/" });
    this.props.functions.changeTitle("URL input");
    this.props.functions.changeRightImage(null);

    this.playUrl = this.playUrl.bind(this);
    this.urlPlay = this.urlPlay.bind(this);
    this.urlChange = this.urlChange.bind(this);
  }

  componentDidMount() {
  }

  componentWillUnmount(){
  }

  urlPlay(url)
  {
      this.viewRef.current.play(url);
  }

  playUrl(instance, url)
  {
    this.setState({loading: true});
    axios.post(window.vars.apiBase + 'play/url?instance=' + instance
    + "&title=" + encodeURIComponent(url)
    + "&url=" + encodeURIComponent(url)).then(
        () => this.setState({loading: false}),
        () => this.setState({loading: false})
        );
  }

  urlChange(value){
    this.setState({url: value});
  }

  render() {
    return (
        <MediaPlayerView ref={this.viewRef} playMedia={this.playUrl}>
          <ViewLoader loading={this.state.loading}/>
          <div className="url-box">
              <div className="url-input">
                <SearchBox placeholder="url of video or torrent" searchTerm={this.state.url} onChange={this.urlChange}/>
              </div>
              <div className="url-play">
                <Button text="play" onClick={(e) => this.urlPlay(this.state.url)} />
              </div>
          </div>
      </MediaPlayerView>
    );
  }
};

export default UrlView;