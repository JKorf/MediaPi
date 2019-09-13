import React, { Component } from 'react';
import axios from 'axios';

import Widget from './Widget.js';
import Switch from './../Components/Switch';
import Socket from './../../Socket2.js';

class TradfriWidget extends Component {
  constructor(props) {
    super(props);

    this.state = {groups: []};
    this.getSize = this.getSize.bind(this);
    this.devicesUpdate = this.devicesUpdate.bind(this);
  }

  shouldShow(){
    return true;
  }


  getSize(){
    return {width: 180, height: 135};
  }

  componentDidMount() {
    this.devicesSub = Socket.subscribe("devices", this.devicesUpdate);
  }

  componentWillUnmount(){
    Socket.unsubscribe(this.devicesSub);
  }

  devicesUpdate(subId, data){
    this.setState({groups: data.groups});
  }

  toggleGroup(group, value)
  {
    console.log("Change " + group.name + " to " + value);
    group.state = value;
    this.updateGroup(group);
    axios.post(window.vars.apiBase + 'home/set_group?group_id=' + group.id + "&state=" + value);
  }

  updateGroup(group)
  {
      var currentGroups = this.state.groups;
      var index = currentGroups.indexOf(group);
      currentGroups.splice(index, 1);
      currentGroups.splice(index, 0, group);
      this.setState({groups: currentGroups});
  }

  render() {
    return (
      <Widget {...this.props} >
        <div className="light-widget-content">
            { this.state.groups.map(group => {
                return(
                    <div key={group.id} className="light-widget-group">
                        <div className="light-widget-group-name truncate">{group.name}</div>
                        <div className="light-widget-group-state"><Switch value={group.state} onToggle={(value) => this.toggleGroup(group, value)} /></div>
                    </div>
                );
            }) }
        </div>
      </Widget>
    );
  }
};

export default TradfriWidget;