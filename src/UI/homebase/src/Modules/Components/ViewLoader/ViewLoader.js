import React, { Component } from 'react';
import loaderImage from "./../../../Images/loader.svg";
import SvgImage from "./../SvgImage";

class ViewLoader extends Component {

  render() {
    if(!this.props.loading)
        return null;

    return <div className="view-loader-wrapper">
        { this.props.loading &&
            <div className="view-loader">
                <SvgImage src={loaderImage} />
                { this.props.text && <div className="view-loader-details">{this.props.text}</div>}
            </div>
        }</div>
  }
};

export default ViewLoader;