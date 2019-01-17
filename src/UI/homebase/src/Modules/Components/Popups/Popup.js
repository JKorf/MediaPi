import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";
import SvgImage from "./../SvgImage";

import loaderImage from "./../../../Images/loader.svg";

class Popup extends Component {
  constructor(props) {
    super(props);
    this.classId = this.props.classId;
    if (!this.classId)
        this.classId = "";
  }

  componentDidMount() {
  }

  componentWillUnmount() {
  }

  render() {
    const loading = this.props.loading;
    const title = this.props.title;
    const children = this.props.children;
    const classId = this.props.classId;

    return (
            <div>
              <div className="popup-background"></div>
              <div className={classId + " popup-window"} onClick={(e) => e.preventDefault()}>
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
          </div>
        );
  }
};
export default Popup;