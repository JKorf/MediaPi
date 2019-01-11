import React, { Component } from 'react';

class SelectionBox extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
        <div className="selection-box">
            <div className="selection-box-title">{this.props.title}</div>
            { this.props.options.map((o) => (
                <div className="selection-box-option" onClick={() => this.props.onChange(o[0])}>
                    <div className="selection-box-option-radio"><input value={o[0]} type="radio" checked={this.props.value == o[0]} /></div>
                    <div className="selection-box-option-title">{o[1]}</div>
                </div> )
            ) }
        </div>
    )
  }
}

export default SelectionBox;