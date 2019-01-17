import React, { Component } from 'react';

class Widget extends Component {
  constructor(props) {
    super(props);

    this.state = {};
  }

  render() {
    const children = this.props.children;
    if (!this.props.dashboard.current)
        return "";

    const dashboardWidth = this.props.dashboard.current.clientWidth;
    const columnWidth = dashboardWidth / 8;

    console.log(dashboardWidth + " / " + columnWidth);

    let style = {
        width: (this.props.width * columnWidth - 20) + "px",
        height: (this.props.height * columnWidth - 20) + "px",
        left: (this.props.x * columnWidth) + "px",
        top: (this.props.y * columnWidth) + "px",
    };

    return (
      <div className={"widget " + (this.props.title ? "with-title": "")} style={style}>
        { this.props.title && <div className="widget-title">{this.props.title}</div>}
        <div className="widget-content">{children}</div>
      </div>
    );
  }
};

export default Widget;