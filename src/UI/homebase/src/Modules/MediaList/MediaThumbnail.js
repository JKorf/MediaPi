import React, { Component } from 'react';

import ColorIndicator from './../Components/ColorIndicator'
import SvgImage from './../Components/SvgImage';
import ratingImage from './../../Images/rating.svg';

class MediaThumbnail extends Component {
  constructor(props) {
    super(props);
    this.lastScrollEvent = new Date();
    this.state = {pointer: false};
  }

  handleScroll = (e) => {
    if(new Date().getTime() - this.lastScrollEvent.getTime() < 1000)
        return;

    const bottom = (e.target.scrollHeight - 100) - e.target.scrollTop <= e.target.clientHeight;
    if (bottom) {
        this.lastScrollEvent = new Date();
        this.props.onScrollBottom();
    }
  }

  SetPointer(newState){
        this.setState({pointer: newState});
    }

  render () {
      return (
          <div className={"media-thumbnail " + (this.state.pointer? "pointer-down": "")} onPointerEnter={() => this.SetPointer(true)}
            onPointerLeave={() =>  this.SetPointer(false)}>
            <img className="media-thumbnail-img" alt="Media thumbnail" src={this.props.img} />
            <div className="media-thumbnail-info">
                <div className="media-thumbnail-info-title truncate2"><span>{this.props.title}</span></div>
                { this.props.rating && <div className="media-thumbnail-info-rating">
                        <div className="media-thumbnail-info-rating-text"><ColorIndicator value={this.props.rating}>{this.props.rating}%</ColorIndicator></div>
                        <div className="media-thumbnail-info-rating-img"><SvgImage src={ratingImage} /></div>
                    </div>
                }
            </div>
          </div> )
  }
}

export default MediaThumbnail;