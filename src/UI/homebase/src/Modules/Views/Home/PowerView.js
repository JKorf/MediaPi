import React, { Component } from 'react';
import axios from 'axios';
import { ResponsiveContainer, LineChart, LabelList, XAxis, YAxis, Tooltip, Legend, Line } from 'recharts';

import ViewLoader from './../../Components/ViewLoader';
import Button from './../../Components/Button';

class PowerView extends Component {
  constructor(props) {
    super(props);
    this.state = {loading: true};
    this.hoursAgo = 0;

    this.props.functions.changeBack({ to: "/home/" });
    this.props.functions.changeTitle("Power usage");
    this.props.functions.changeRightImage(null);
  }

  componentDidMount() {
    this.getData();
  }

  getData(){
    this.setState({loading: true});
    axios.get(window.vars.apiBase + 'toon/electricity?startHours=' + -(this.hoursAgo - 8) + "&endHours=" + -this.hoursAgo).then(
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
        { this.state.powerData &&
            <div>
                <div className="graph-navigation">

                    <div className="graph-back" onClick={() => this.back()}><Button text="-8 hours" classId="secondary"/></div>
                    <div className="graph-forward" onClick={() => this.next()}><Button text="+8 hours" classId="secondary"/></div>
                </div>

                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={this.state.powerData} margin={{top:20,right:10,bottom:20,left:-20}}>
                      <XAxis angle={60}
                             dy={20}
                             interval="preserveStartEnd"
                             tickFormatter = {(min5) => new Intl.DateTimeFormat('en-GB', {hour: '2-digit', minute: '2-digit' }).format(new Date(1970, 0, 0).setTime(this.firstTime + min5 * (1000*60*5)))}/>
                      <YAxis dataKey="value" unit={this.state.powerData[0].unit} />
                      <Line dataKey="value" stroke="#8884d8" dot={false} animationDuration={500} />
                                            <Tooltip />

                    </LineChart>
                </ResponsiveContainer>
            </div>
        }
      </div>
    );
  }
};

export default PowerView;