import React, { Component } from 'react';

class CheckBox extends Component {
  constructor(props) {
    super(props);
    this.changeValue = this.changeValue.bind(this);
  }

  changeValue()
  {
    if (this.props.readonly)
        return;
    this.props.onChange(!this.props.value);
  }

  render(){
    return (
      <div className="checkbox">
        <div className="checkbox-inner" onClick={() => this.changeValue()}>
            { this.props.value &&
                <div className="checkbox-check">x</div>
            }
        </div>
      </div>)
  }
}

export default CheckBox;