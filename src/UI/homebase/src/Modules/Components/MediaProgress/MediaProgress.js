import React, { Component } from 'react';

class MediaProgress extends Component {

  render() {
    return <div className="media-progress-background"><div className="media-progress" style={{width: "calc(" + this.props.percentage + "% + 16px"}} ></div></div>
  }
}

export default MediaProgress;