import React, { Component } from 'react';

class Widget extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    const children = this.props.children;
    return (
      <div className="widget">
       {children}
      </div>
    );
  }
};

export default Widget;