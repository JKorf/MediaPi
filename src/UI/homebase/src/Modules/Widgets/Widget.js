import React, { Component } from 'react';
import { Link } from "react-router-dom";

import SvgImage from "./../Components/SvgImage";

import loaderImage from "./../../Images/loader.svg";

class Widget extends Component {
  constructor(props) {
    super(props);
    this.state = {};
  }

  render() {
    const children = this.props.children;

    var title = "";
    if(this.props.title)
        title = <div className="widget-title">{this.props.title}</div>;
    if (this.props.titleLink)
        title = <Link to={this.props.titleLink}>{title}</Link>;

    return (
      <div ref={this.widgetRef} className={"widget " + (this.props.title ? "with-title": "")} >
        { title }
        { this.props.loading && <div className="popup-loader"><SvgImage src={loaderImage} /></div> }
        <div className="widget-content">{children}</div>
      </div>
    );
  }
};

export default Widget;