import React, { Component } from 'react';

import Button from './../../Components/Button';
import UsageGraph from './../../Components/UsageGraph';

class UsageView extends Component {
  constructor(props) {
    super(props);
    var time = new Date().getTime();
    this.state = {loading: true, interval: "hours", type: this.props.type};
    var t = (this.props.type === "power"? "Power": "Gas");
    this.props.functions.changeBack({ to: "/home/" });
    this.props.functions.changeTitle( t + " usage stats");
    this.props.functions.changeRightImage(null);
  }

  componentDidMount() {
      this.changeInterval("hours");
  }

  back(){
    var change = this.getTicks(this.state.interval) *  this.getTimespan(this.state.interval);
    console.log("Start: " + new Date(this.state.startTime - change) + ", end: " + new Date( this.state.endTime - change));
    this.setState({startTime: this.state.startTime - change, endTime: this.state.endTime - change});
  }

  next(){
      var change = this.getTicks(this.state.interval) *  this.getTimespan(this.state.interval);
      console.log("Start: " + new Date(this.state.startTime + change) + ", end: " + new Date( this.state.endTime + change));
      this.setState({startTime: this.state.startTime + change, endTime: this.state.endTime + change});
  }

  changeInterval(newInterval){
    var endTime = this.ceilDate(new Date(), this.getTimespan(newInterval)).getTime();
    var startTime = 0;
    if (newInterval == "minutes"){
        startTime = endTime - this.getTicks(newInterval) * this.getTimespan(newInterval);
    }
    else if(newInterval == "hours"){
        startTime = endTime - this.getTicks(newInterval) * this.getTimespan(newInterval);
    }
    else if(newInterval == "days"){
        startTime = endTime - this.getTicks(newInterval) * this.getTimespan(newInterval);
    }
    else if(newInterval == "months"){
        startTime = endTime - this.getTicks(newInterval) * this.getTimespan(newInterval);
    }
    else if(newInterval == "years"){
        startTime = endTime - this.getTicks(newInterval) * this.getTimespan(newInterval);
    }
    endTime -= 1000;
    this.setState({interval: newInterval, startTime: startTime, endTime: endTime, loading: false});
  }

  getTimespan(interval)
  {
    if (interval == "minutes")
        return 5 * 60 * 1000;
    else if(interval == "hours")
        return 60 * 60 * 1000;
    else if(interval == "days")
        return 24 * 60 * 60 * 1000;
    else if(interval == "months")
        return 30 * 24 * 60 * 60 * 1000;
    else if(interval == "years")
        return 365 * 24 * 60 * 60 * 1000;
  }

  getTicks(interval){
   if (interval == "minutes")
        return 48;
    else if(interval == "hours")
        return 12;
    else if(interval == "days")
        return 14;
    else if(interval == "months")
        return 12;
    else if(interval == "years")
        return 3;
  }

  ceilDate(date, period) {
    return new Date(Math.ceil(date.getTime() / period ) * period);
  }

  render() {

    return (
      <div className="gas-view">
         <div className="graph-navigation">
            <div className="graph-back" onClick={() => this.back()}><Button text="<" classId="secondary"/></div>
            <div className="graph-forward" onClick={() => this.next()}><Button text=">" classId="secondary"/></div>
            <div className="graph-interval">
                <select value={this.state.interval} onChange={(e) => this.changeInterval(e.target.value)}>
                    <option value="minutes">minutes</option>
                    <option value="hours">hours</option>
                    <option value="days">days</option>
                    <option value="months">months</option>
                    <option value="years">years</option>
                </select>
            </div>
        </div>
        { !this.state.loading &&
            <UsageGraph type={this.state.type} startTime={this.state.startTime} endTime={this.state.endTime} interval={this.state.interval} height={300} />
        }
      </div>
    );
  }
};

export default UsageView;