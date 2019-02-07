import React, { Component } from 'react';
import { Link } from "react-router-dom";

import Widget from './Widget.js';

class TestWidget extends Component {
  constructor(props) {
    super(props);

    this.getSize = this.getSize.bind(this);
  }


  getSize(){
    return {width: 120, height: 50};
  }

  componentDidMount() {
  }

  componentWillUnmount(){
  }

  render() {
    return (
      <Widget {...this.props}>
        TestWidget!
      </Widget>
    );
  }
};

export default TestWidget;