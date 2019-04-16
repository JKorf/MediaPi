import React, { Component } from 'react';

class SwitchBoxItem extends Component {

  render() {
    return (
        <div className={"switch-box-item " + (this.props.selected ? "selected": "")} onClick={() => this.props.onClick()}>
            {this.props.text}
        </div>
    )
  }
}

export default SwitchBoxItem;