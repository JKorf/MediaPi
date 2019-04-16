import React, { Component } from 'react';

class SwitchBox extends Component {

  render() {
    return (
        <div className="switch-box" >
            {this.props.children}
        </div>
    )
  }
}

export default SwitchBox;