import React, { Component } from 'react';

class Switch extends Component {

  render() {
    return (
        <div className={"switch " + (this.props.value?"on":"off")} onClick={() => this.props.onToggle(!this.props.value)}>
            <div className="switch-inner"></div>
        </div>
    )
  }
}

export default Switch;