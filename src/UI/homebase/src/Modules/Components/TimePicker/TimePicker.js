import React, { Component } from 'react';

class TimePicker extends Component {
  constructor(props) {
    super(props);

    this.hourValues = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23];
    this.minuteValues = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55];
  }

  addLeadingZero(value)
  {
    if (value >= 10)
        return value;
    return "0" + value;
  }

  render(){
    return (
      <div className="time-picker">
        <select className="hour-picker" value={this.props.hour} onChange={(e) => this.props.onHourChange(e.target.value)}>
            { this.hourValues.map(h =>
                <option key={h} value={h}>{this.addLeadingZero(h)}</option>
            )}
        </select>
         :
        <select className="minute-picker" value={this.props.minute} onChange={(e) => this.props.onMinuteChange(e.target.value)}>
            { this.minuteValues.map(m =>
                <option key={m} value={m}>{this.addLeadingZero(m)}</option>
            )}
        </select>
      </div>)
  }
}

export default TimePicker;