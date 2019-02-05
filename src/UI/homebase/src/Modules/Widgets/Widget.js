import React, { Component } from 'react';

class Widget extends Component {
  constructor(props) {
    super(props);
    this.state = {};
  }

  render() {
    const children = this.props.children;

    return (
      <div ref={this.widgetRef} className={"widget " + (this.props.title ? "with-title": "")} >
        { this.props.title && <div className="widget-title">{this.props.title}</div>}
        <div className="widget-content">{children}</div>
      </div>
    );
  }
};

export default Widget;