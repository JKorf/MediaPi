import React, { Component } from 'react';
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
                <div className="popup-title">{title}</div>
                <div className="popup-content">
                    { loading && <div className="popup-loader"><SvgImage src={loaderImage} /></div> }
                    { !loading && children}
                </div>
                <div className="popup-buttons">{this.props.buttons}</div>
              </div>
          </div>
        );
  }
};
export default Popup;