import React, { Component } from 'react';
import axios from 'axios';
import { ResponsiveContainer, LineChart, XAxis, YAxis, Tooltip, Line } from 'recharts';
import { formatTime } from './../../../Utils/Util.js';

import ViewLoader from './../../Components/ViewLoader';

class PowerUsageGraph extends Component {
  constructor(props){
      super(props);

      this.state = {loading: true};
  }

  componentDidMount(){
    this.getData();
  }

  componentDidUpdate(prevProps) {
    if(this.props.hoursAgo !== prevProps.hoursAgo)
        this.getData();
  }

  componentWillUnmount(){
  }

  getData(){
    this.setState({loading: true});
    axios.get(window.vars.apiBase + 'home/get_gas_usage?startHours=' + -(this.props.hoursAgo - 8) + "&endHours=" + -this.props.hoursAgo).then(
        (data) => {
            this.setState({loading: false});
            if (!data.data || !data.data.hours || data.data.hours.length === 0)
                return;

            if (data.data.hours.length === 0){
                this.hoursAgo -= 8;
                return;
            }

            this.firstTime = data.data.hours[0].timestamp;
            this.setState({powerData: data.data.hours});
            console.log(data.data);
         },
        (error) =>
        {
            this.setState({loading: false});
            console.log(error);
        }
    )
  }

  render() {
    return (<div>
        <ViewLoader loading={this.state.loading}/>
        { this.state.powerData &&
            <div className="gas-graph-container">
            <ResponsiveContainer width="100%" height={this.props.height}>
                <LineChart data={this.state.powerData} margin={{top:20,right:10,bottom:20,left:0}}>
                  <XAxis angle={60}
                         dy={20}
                         interval="preserveStartEnd"
                         tickFormatter = {(min5) => formatTime(this.firstTime + min5 * (1000*60*5), false, false, false, true, true)}/>
                  <YAxis dataKey="value" unit={this.state.powerData[0].unit} />
                  <Line dataKey="value" stroke="#8884d8" dot={false} animationDuration={500} />
                  <Tooltip labelFormatter={(value, name, props) => formatTime(this.firstTime + value * (1000*60*5), false, true, true, true, true)} />

                </LineChart>
            </ResponsiveContainer>
            </div>
        }
    </div>);
  }
}

export default PowerUsageGraph;