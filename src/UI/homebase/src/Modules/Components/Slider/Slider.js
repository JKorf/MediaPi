import React, { Component } from 'react';

class Slider extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    const min = this.props.min;
    const max = this.props.max;
    const value = this.props.value;
    const percentage = (max - min) / value;

    return (
        <div className="slider">
            <div className="slider-background"></div>
            <div className="slider-thumb" style={{left: "calc(" + percentage + "% - 5px"}} ></div>
        </div>
    )
  }
}

export default Slider;