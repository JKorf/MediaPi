import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";
import SvgImage from "./../SvgImage";

import loaderImage from "./../../../Images/loader.svg";

class Popup extends Component {
  constructor(props) {
    super(props);
  }

  componentDidMount() {
  }

  componentWillUnmount() {
  }

  render() {
    const loading = this.props.loading;
    const title = this.props.title;
    const children = this.props.children;

    return (
          <div className="popup-window">
            { loading &&
                <div className="popup-loader"><SvgImage src={loaderImage} /></div>
            }
            { !loading && (
                <div className="pupup-inner">
                    <div className="popup-title">{title}</div>
                    <div className="popup-content">{children}</div>
                    <div className="popup-buttons">{this.props.buttons}</div>
                </div>
            )}
          </div>
        );
  }
};
export default Popup;