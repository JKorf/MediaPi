import React, { Component } from 'react';
import axios from 'axios';
import { ResponsiveContainer, LineChart, Line, BarChart, LabelList, XAxis, YAxis, Tooltip, Bar } from 'recharts';
import ViewLoader from './../../Components/ViewLoader';
import { formatTime } from './../../../Utils/Util.js';

class UsageGraph extends Component {
  constructor(props){
      super(props);

      this.valueKey = "value";
      this.state = {loading: true};
      this.getTickLabel = this.getTickLabel.bind(this);
  }

  componentDidMount(){
    this.getData();
  }

  componentDidUpdate(prevProps) {
    if(this.props.startTime !== prevProps.startTime || this.props.interval !== prevProps.interval)
        this.getData();
  }

  componentWillUnmount(){
  }

  getData(){
    this.setState({loading: true});

    axios.get(window.vars.apiBase + 'home/get_usage_stats?type=' + this.props.type + '&startTime=' + this.props.startTime + "&endTime=" + this.props.endTime + "&interval=" + this.props.interval).then(
        (data) => {
            this.setState({loading: false});
            if (!data.data || data.data.length === 0)
                return;

            this.firstTime = data.data[0].timestamp;
            this.setState({usageData: data.data});
            console.log(data.data);
         },
        (error) =>
        {
            console.log(error);
            this.setState({loading: false});
         }
    )
  }

  getTickLabel(tickNumber){
    if(this.props.interval == "minutes")
        return formatTime(this.firstTime + tickNumber * (1000*60*5), false, false, false, true, true);
    else if(this.props.interval == "hours")
        return formatTime(this.firstTime + tickNumber * (1000*60*60), false, false, false, true, true);
    else if(this.props.interval == "days")
        return formatTime(this.firstTime + tickNumber * (1000*60*60*24), false, true, true, false, false);
    else if(this.props.interval == "months")
        return formatTime(this.firstTime + tickNumber * (1000*60*60*24*31), false, true, false, false, false);
    else if(this.props.interval == "years")
        return formatTime(this.firstTime + tickNumber * (1000*60*60*24*365), true, false, false, false, false);
  }

  render() {
    return (<div>
        <ViewLoader loading={this.state.loading}/>
        { this.state.usageData && this.state.usageData.length > 0 &&
        <div className="gas-graph-container">
            { this.props.interval == "minutes" &&
                <ResponsiveContainer minHeight={this.props.height}>
                    <LineChart data={this.state.usageData} margin={{top:30,right:10,bottom:20,left:0}}>
                      <XAxis angle={60}
                             dy={20}
                             tickFormatter={this.getTickLabel}/>
                      <YAxis dataKey={this.valueKey} unit={this.state.usageData[0].unit}/>
                      <Tooltip labelFormatter={this.getTickLabel} />
                      <Line dataKey={this.valueKey} fill="#8884d8" animationDuration={500}>
                      </Line>
                    </LineChart>
                </ResponsiveContainer>
            }
            { this.props.interval != "minutes" &&
                <ResponsiveContainer minHeight={this.props.height}>
                    <BarChart data={this.state.usageData} margin={{top:30,right:10,bottom:20,left:0}}>
                      <XAxis angle={60}
                             dy={20}
                             minTickGap={0}
                             interval={0}
                             tickCount={8}
                             tickFormatter={this.getTickLabel}/>
                      <YAxis dataKey={this.valueKey} unit={this.state.usageData[0].unit} />
                      <Tooltip labelFormatter={this.getTickLabel} />
                      <Bar dataKey={this.valueKey} fill="#8884d8" animationDuration={500}>
                        <LabelList fill="#222" dataKey={this.valueKey} position="top" offset={10} />
                      </Bar>
                    </BarChart>
                </ResponsiveContainer>
            }
        </div>
        }
    </div>);
  }
}

export default UsageGraph;