import React, { Component } from 'react';
import { Link } from "react-router-dom";
import axios from 'axios';

import Widget from './Widget.js';
import Switch from './../Components/Switch';

class LightWidget extends Component {
  constructor(props) {
    super(props);

    this.state = {};
    this.getSize = this.getSize.bind(this);
  }


  getSize(){
    return {width: 180, height: 135};
  }

  componentDidMount() {
    axios.get(window.vars.apiBase + 'lighting/get_groups').then(
        (data) => {
            this.setState({lightData: data.data});
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
      const lightData = state.lightData.map(s => {
        if(s.id === group.id){
            s.state = value;
        }
        return s;
      });

      return {
        lightData,
      };
    });
    axios.post(window.vars.apiBase + 'lighting/set_group_state?group='+group.id+'&state=' + value);
  }

  render() {
    return (
      <Widget {...this.props} loading={!this.state.lightData}>
        { this.state.lightData &&
            <div className="light-widget-content">
                { this.state.lightData.map(lightGroup => {
                    return(
                        <div key={lightGroup.id} className="light-widget-group">
                            <div className="light-widget-group-name truncate">{lightGroup.name}</div>
                            <div className="light-widget-group-state"><Switch value={lightGroup.state} onToggle={(value) => this.toggleGroup(lightGroup, value)} /></div>
                        </div>
                    );
                }) }
            </div>
         }
      </Widget>
    );
  }
};

export default LightWidget;