import React, { Component } from 'react';

import ViewLoader from './../../Components/ViewLoader';
import Button from './../../Components/Button';
import UsageGraph from './../../Components/UsageGraph';

class PowerView extends Component {
  constructor(props) {
    super(props);
    this.state = {loading: true, hoursAgo: 0};

    this.props.functions.changeBack({ to: "/home/" });
    this.props.functions.changeTitle("Power usage");
    this.props.functions.changeRightImage(null);
  }

  back(){
    this.setState({hoursAgo: this.state.hoursAgo - 8});
  }

  next(){
    this.setState({hoursAgo: this.state.hoursAgo + 8});
  }

  render() {

    return (
      <div className="power-view">
        <ViewLoader loading={false}/>
        <div className="graph-navigation">
            <div className="graph-back" onClick={() => this.back()}><Button text="-8 hours" classId="secondary"/></div>
            <div className="graph-forward" onClick={() => this.next()}><Button text="+8 hours" classId="secondary"/></div>
        </div>

        <UsageGraph type="power" startTime={this.state.startTime} endTime={this.state.endTime} interval={this.state.interval} height={300}/>

      </div>
    );
  }
};

export default PowerView;