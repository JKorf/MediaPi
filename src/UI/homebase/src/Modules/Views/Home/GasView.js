import React, { Component } from 'react';

import Button from './../../Components/Button';
import GasUsageGraph from './../../Components/GasUsageGraph';

class GasView extends Component {
  constructor(props) {
    super(props);
    this.state = {loading: true, hoursAgo: 0};

    this.props.functions.changeBack({ to: "/home/" });
    this.props.functions.changeTitle("Gas usage");
    this.props.functions.changeRightImage(null);
  }

  componentDidMount() {
  }

  back(){
    this.setState({hoursAgo: this.state.hoursAgo - 8});
  }

  next(){
      this.setState({hoursAgo: this.state.hoursAgo + 8});
  }

  render() {

    return (
      <div className="heating-view">
         <div className="graph-navigation">
            <div className="graph-back" onClick={() => this.back()}><Button text="-8 hours" classId="secondary"/></div>
            <div className="graph-forward" onClick={() => this.next()}><Button text="+8 hours" classId="secondary"/></div>
        </div>

        <GasUsageGraph hoursAgo={this.state.hoursAgo} height={300} />
      </div>
    );
  }
};

export default GasView;