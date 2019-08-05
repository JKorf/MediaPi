import React, { Component } from 'react';
import axios from 'axios';

import Widget from './Widget.js';
import Switch from './../Components/Switch';

class TradfriWidget extends Component {
  constructor(props) {
    super(props);

    this.state = {};
    this.getSize = this.getSize.bind(this);
  }

  shouldShow(){
    return true;
  }


  getSize(){
    return {width: 180, height: 135};
  }

  componentDidMount() {
    axios.get(window.vars.apiBase + 'tradfri/groups').then(
        (data) => {
            this.setState({tradfriData: data.data});
            console.log(data.data);
         },
        (error) => { console.log(error) }
    )
  }

  componentWillUnmount(){
  }

  toggleGroup(group, value)
  {
    console.log("Change " + group.name + " to " + value);
    this.setState(state => {
      const tradfriData = state.tradfriData.map(s => {
        if(s.id === group.id){
            s.state = value;
        }
        return s;
      });

      return {
        tradfriData,
      };
    });
    axios.post(window.vars.apiBase + 'tradfri/group_state?group_id='+group.id+'&state=' + value);
  }

  render() {
    return (
      <Widget {...this.props} loading={!this.state.tradfriData}>
        { this.state.tradfriData &&
            <div className="light-widget-content">
                { this.state.tradfriData.map(group => {
                    return(
                        <div key={group.id} className="light-widget-group">
                            <div className="light-widget-group-name truncate">{group.name}</div>
                            <div className="light-widget-group-state"><Switch value={group.state} onToggle={(value) => this.toggleGroup(group, value)} /></div>
                        </div>
                    );
                }) }
            </div>
         }
      </Widget>
    );
  }
};

export default TradfriWidget;