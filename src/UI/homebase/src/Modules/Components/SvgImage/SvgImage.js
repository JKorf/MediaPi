import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";
import axios from 'axios';

class SvgImage extends Component {
  constructor(props) {
    super(props);
    this.state = {svg: "<div></div>"};
  }

  componentDidMount() {
    this.unmounted = false;
    axios.get(this.props.src).then((data) => {
        if(!this.unmounted)
            this.setState({svg: data.data});
    });
  }

  componentWillUnmount(){
    this.unmounted = true;
  }

  render() {
    const svg = this.state.svg;
    return (
        <div className="svg-image" dangerouslySetInnerHTML={{__html: svg}}></div>
    );
  }
};

export default SvgImage;