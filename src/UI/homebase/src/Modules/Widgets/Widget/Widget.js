import React, { Component } from 'react';

class Widget extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    const children = this.props.children;
    const title = this.props.title;
    return (
      <div className="widget">
        <div className="widget-title">{title}</div>
        <div className="widget-content">{children}</div>
      </div>
    );
  }
};

export default Widget;