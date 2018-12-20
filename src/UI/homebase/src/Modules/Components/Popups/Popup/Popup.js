import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";

class Popup extends Component {
  constructor(props) {
    super(props);
  }

  componentDidMount() {
  }

  componentWillUnmount() {
  }

  render() {
    const title = this.props.title;
    const children = this.props.children;
    let popup = <div></div>
    if (this.props.show)
        popup = (
                  <div className="popup-window">
                    <div className="popup-title">{title}</div>
                    <div className="popup-content">{children}</div>
                  </div>
                );

    return popup;
  }
};
export default Popup;