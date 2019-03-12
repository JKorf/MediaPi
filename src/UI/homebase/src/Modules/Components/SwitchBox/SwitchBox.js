import React, { Component } from 'react';

class SwitchBox extends Component {

 constructor(props) {
    super(props);
  }

  render() {
    return (
        <div className="switch-box" >
            {this.props.children}
        </div>
    )
  }
}

export default SwitchBox;