import React, { Component } from 'react';
import axios from 'axios';
import { ResponsiveContainer, BarChart, LabelList, XAxis, YAxis, Tooltip, Bar } from 'recharts';
import ViewLoader from './../../Components/ViewLoader';
import { formatTime } from './../../../Utils/Util.js';

class GasUsageGraph extends Component {
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
    axios.get(window.vars.apiBase + 'home/get_gas_usage?startHours=' + -(this.props.hoursAgo - 8) + "&endHours=" + this.props.hoursAgo).then(
        (data) => {
            this.setState({loading: false});
            if (!data.data || !data.data.hours || data.data.hours.length === 0)
                return;

            this.firstTime = data.data.hours[0].timestamp;
            this.setState({gasData: data.data.hours});
            console.log(data.data);
         },
        (error) =>
        {
            console.log(error);
            this.setState({loading: false});
         }
    )
  }

  render() {
    return (<div>
        <ViewLoader loading={this.state.loading}/>
        <div className="gas-graph-container">
            <ResponsiveContainer minHeight={this.props.height}>
                <BarChart data={this.state.gasData} margin={{top:30,right:10,bottom:20,left:0}}>
                  <XAxis angle={60}
                         dy={20}
                         minTickGap={0}
                         interval={0}
                         tickCount={8}
                         tickFormatter = {(hour) => formatTime(this.firstTime + hour * (1000*60*60), false, false, false, true, true)}/>
                  <YAxis dataKey="value" unit="L" />
                  <Tooltip labelFormatter={(value, name, props) => formatTime(this.firstTime + value * (1000*60*60), false, true, true, true, true)} />
                  <Bar dataKey="value" fill="#8884d8" animationDuration={500}>
                    <LabelList fill="#222" dataKey="value" position="top" offset={10} />
                  </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    </div>);
  }
}

export default GasUsageGraph;