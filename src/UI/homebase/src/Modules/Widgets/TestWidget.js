import React, { Component } from 'react';
import { Link } from "react-router-dom";

import Widget from './Widget.js';

class TestWidget extends Component {
  constructor(props) {
    super(props);
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