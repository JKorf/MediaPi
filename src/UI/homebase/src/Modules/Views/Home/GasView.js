import React, { Component } from 'react';
import axios from 'axios';
import { ResponsiveContainer, BarChart, LabelList, XAxis, YAxis, Tooltip, Legend, Bar } from 'recharts';

import ViewLoader from './../../Components/ViewLoader';

class GasView extends Component {
  constructor(props) {
    super(props);
    this.state = {loading: true};
    this.hoursAgo = 0;

    this.props.functions.changeBack({ to: "/home/" });
    this.props.functions.changeTitle("Gas usage");
    this.props.functions.changeRightImage(null);
  }

  componentDidMount() {
    this.getData();
  }

  getData(){
    this.setState({loading: true});
    axios.get(window.vars.apiBase + 'toon/gas?startHours=' + -(this.hoursAgo - 8) + "&endHours=" + this.hoursAgo).then(
        (data) => {
            this.setState({loading: false});
            if (data.data.hours.length == 0)
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

  back(){
    this.hoursAgo -= 8;
    this.getData();
  }

  next(){
    this.hoursAgo += 8;
    this.getData();
  }

  render() {

    return (
      <div className="heating-view">
        <ViewLoader loading={this.state.loading}/>
        { this.state.gasData &&
            <div>
                 <div className="graph-navigation">
                    <div className="graph-back" onClick={() => this.back()}>-8 hours</div>
                    <div className="graph-forward" onClick={() => this.next()}>+8 hours</div>
                </div>

                <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={this.state.gasData} margin={{top:20,right:10,bottom:20,left:-20}}>
                      <XAxis angle={60}
                             dy={20}
                             minTickGap={0}
                             interval={0}
                             tickCount={8}
                             tickFormatter = {(hour) => new Intl.DateTimeFormat('en-GB', {hour: '2-digit', minute: '2-digit' }).format(new Date(1970, 0, 0).setTime(this.firstTime + hour * (1000*60*60)))}/>
                      <YAxis dataKey="value" unit="L" />
                      <Tooltip />
                      <Bar dataKey="value" fill="#8884d8" animationDuration={500}>
                        <LabelList fill="#EEE" dataKey="value" position="top"  offset={10} />
                      </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        }
      </div>
    );
  }
};

export default GasView;