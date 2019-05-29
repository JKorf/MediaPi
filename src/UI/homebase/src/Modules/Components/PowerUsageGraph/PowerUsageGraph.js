import React, { Component } from 'react';
import axios from 'axios';
import { ResponsiveContainer, LineChart, LabelList, XAxis, YAxis, Tooltip, Legend, Line } from 'recharts';

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
    if(this.props.hoursAgo != prevProps.hoursAgo)
        this.getData();
  }

  componentWillUnmount(){
  }

  getData(){
    this.setState({loading: true});
    axios.get(window.vars.apiBase + 'toon/electricity?startHours=' + -(this.props.hoursAgo - 8) + "&endHours=" + -this.props.hoursAgo).then(
        (data) => {
            this.setState({loading: false});
            if (data.data.hours.length == 0){
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
            <ResponsiveContainer width="100%" height={this.props.height}>
                <LineChart data={this.state.powerData} margin={{top:20,right:10,bottom:20,left:0}}>
                  <XAxis angle={60}
                         dy={20}
                         interval="preserveStartEnd"
                         tickFormatter = {(min5) => new Intl.DateTimeFormat('en-GB', {hour: '2-digit', minute: '2-digit' }).format(new Date(1970, 0, 0).setTime(this.firstTime + min5 * (1000*60*5)))}/>
                  <YAxis dataKey="value" unit={this.state.powerData[0].unit} />
                  <Line dataKey="value" stroke="#8884d8" dot={false} animationDuration={500} />
                                        <Tooltip />

                </LineChart>
            </ResponsiveContainer>
        }
    </div>);
  }
}

export default PowerUsageGraph;