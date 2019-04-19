import React, { Component } from 'react';
import axios from 'axios';
import Socket from './../../../Socket2.js';

import { InfoGroup } from './../../Components/InfoGroup';
import ViewLoader from './../../Components/ViewLoader';
import Slider from './../../Components/Slider';
import Switch from './../../Components/Switch';
import socketIcon from './../../../Images/socket.svg';
import lightIcon from './../../../Images/bulb.svg';

class TradfriView extends Component {
  constructor(props) {
    super(props);
    this.state = {};

    this.props.functions.changeBack({ to: "/home/" });
    this.props.functions.changeTitle("Lights & sockets");
    this.props.functions.changeRightImage(null);
    this.updateGroup = this.updateGroup.bind(this);
    this.tradfriUpdate = this.tradfriUpdate.bind(this);
  }

  componentDidMount() {
    this.tradfriSub = Socket.subscribe("tradfri", this.tradfriUpdate);

//    axios.get(window.vars.apiBase + 'lighting/get_groups').then(
//        (data) => {
//            this.setState({lightData: data.data});
//            console.log(data.data);
//         },
//        (error) => { console.log(error) }
//    )
  }

  componentWillUnmount(){
    Socket.unsubscribe(this.tradfriSub);
  }

  tradfriUpdate(subId, data){
    console.log("Tradfri update: ", data);
    this.setState({tradfriData: data.groups})
  }

  writeDimmerPercentage(value)
  {
    return Math.round(value / 255 * 100) + "%";
  }

  writeWarmthPercentage(value)
  {
    return Math.round((value - 250) / 204 * 100) + "%";
  }

  dimmerChange(group, value)
  {
    value = Math.round(value);
    console.log("Change " + group.name + " to " + value);
    this.updateGroup(group.id, "dimmer", value);
    axios.post(window.vars.apiBase + 'tradfri/group_dimmer?group_id='+group.id+'&dimmer=' + value);
  }

  toggleGroup(group, value)
  {
    console.log("Change " + group.name + " to " + value);
    this.updateGroup(group.id, "state", value);
    axios.post(window.vars.apiBase + 'tradfri/group_state?group_id='+group.id+'&state=' + value);
  }

  lightDimmerChange(group, light, value)
  {
    value = Math.round(value);
    console.log("Change " + light.name + " dimmer to " + value);
    this.updateDevice(group.id, light.id, "dimmer", value);
    axios.post(window.vars.apiBase + 'tradfri/light_dimmer?device_id='+light.id+'&dimmer=' + value);
  }

  lightWarmthChange(group, light, value)
  {
    value = Math.round(value);
    console.log("Change " + light.name + " warmth to " + value);
    this.updateDevice(group.id, light.id, "color_temp", value);
    axios.post(window.vars.apiBase + 'tradfri/light_warmth?device_id='+light.id+'&warmth=' + value);
  }

  toggleLight(group, light, value)
  {
    console.log("Change " + light.name + " to " + value);
    this.updateDevice(group.id, light.id, "state", value);
    axios.post(window.vars.apiBase + 'tradfri/device_state?device_id='+light.id+'&state=' + value);
  }

  groupTitleChange(group, newTitle)
  {
    this.updateGroup(group.id, "name", newTitle);
  }

  groupTitleSave(group, newTitle)
  {
      axios.post(window.vars.apiBase + 'tradfri/group_name?group_id='+group.id+'&name=' + encodeURIComponent(newTitle));
  }

  deviceTitleChange(group, device, newTitle)
  {
    this.setState(state =>
    ({
        tradfriData: state.tradfriData.map(s => {
            if(s.id === group.id){
                for(var i = 0; i < s.devices.length; i++)
                {
                    if(s.devices[i].id === device.id){
                        s.devices[i].name = newTitle;
                    }
                }
            }
            return s;
        })
    }));
  }

  deviceTitleSave(device, newTitle)
  {
      axios.post(window.vars.apiBase + 'tradfri/device_name?device_id='+device.id+'&name=' + encodeURIComponent(newTitle));
  }

  toggleGroupDetails(group)
  {
    group.showDetails = !group.showDetails;
    this.updateGroup(group.id, "showDetails", group.showDetails);

    if(group.showDetails){
        console.log("request device data for group " + group.name);
        axios.get(window.vars.apiBase + 'tradfri/group_devices?group_id='+group.id).then(
            (data) => { console.log(data.data); return this.updateGroup(group.id, "devices", data.data); },
            (err) => { console.log (err) }
        )
    }
  }

  updateGroup(groupId, property, value)
  {
    this.setState(state =>
    ({
        tradfriData: state.tradfriData.map(s => {
            if(s.id === groupId)
                s[property] = value;
            return s;
        })
    }));
  }

  updateDevice(groupId, deviceId, property, value)
  {
    this.setState(state =>
    ({
        tradfriData: state.tradfriData.map(s => {
            if(s.id === groupId){
                for(var i = 0; i < s.devices.length; i++)
                {
                    if(s.devices[i].id === deviceId){
                        s.devices[i].items[0][property] = value;
                    }
                }
            }
            return s;
        })
    }));
  }

  render() {
    return (
      <div className="lighting-view">
        <ViewLoader loading={!this.state.tradfriData}/>
        { this.state.tradfriData &&
            this.state.tradfriData.map(deviceGroup => {
                return(
                    <div key={deviceGroup.id} className="light-group">
                        <InfoGroup title={deviceGroup.name}
                                   titleChangeable={true}
                                   onTitleClick={() => this.toggleGroupDetails(deviceGroup)}
                                   onTitleChange={(title) => this.groupTitleChange(deviceGroup, title)}
                                   onSave={(title) => this.groupTitleSave(deviceGroup, title)}>
                           <div className="light-group-content">
                                <div className="light-group-dimmer">
                                    <Slider format={this.writeDimmerPercentage} formatMinMax={(value) => value === 0 ? "Dimmer": "" } min={0} max={255} value={deviceGroup.dimmer} onChange={(value) => this.dimmerChange(deviceGroup, value)} />
                                </div>
                                <div className="light-group-state"><Switch value={deviceGroup.state} onToggle={(value) => this.toggleGroup(deviceGroup, value)} /></div>
                            </div>
                            <div className="device-group-devices-header" onClick={() => this.toggleGroupDetails(deviceGroup)}>{ deviceGroup.device_count } devices</div>
                            { deviceGroup.showDetails &&
                                <div className="light-group-details">
                                    { deviceGroup.devices &&
                                        deviceGroup.devices.map(device => {
                                            return (
                                                <InfoGroup key={device.id}
                                                           icon={(device.can_set_dimmer || device.can_set_temp ? lightIcon : socketIcon)}
                                                           title={device.name}
                                                           titleChangeable={true}
                                                           onTitleChange={(title) => this.deviceTitleChange(deviceGroup, device, title)}
                                                           onSave={(title) => this.deviceTitleSave(device, title)}>
                                                     <div className="light-group-light" key={device.id}>
                                                        <div className="light-group-state"><Switch value={device.items[0].state} onToggle={(value) => this.toggleLight(deviceGroup, device, value)} /></div>

                                                        { (device.can_set_dimmer || device.can_set_temp) &&
                                                            <div className="device-group-controls">
                                                                { device.can_set_dimmer &&
                                                                 <div className="light-group-dimmer">
                                                                    <Slider format={this.writeDimmerPercentage} formatMinMax={(value) => value === 0 ? "Dimmer": "" } min={0} max={255} value={device.items[0].dimmer} onChange={(value) => this.lightDimmerChange(deviceGroup, device, value)} />
                                                                </div>
                                                                }
                                                                { device.can_set_temp &&
                                                                    <div className="light-group-warmth">
                                                                        <Slider format={this.writeWarmthPercentage} formatMinMax={(value) => value === 250 ? "Warmth": "" } min={250} max={454} value={device.items[0].color_temp} onChange={(value) => this.lightWarmthChange(deviceGroup, device, value)} />
                                                                    </div>
                                                                }
                                                            </div>
                                                        }
                                                    </div>
                                                </InfoGroup>

                                            )
                                        })

                                    }
                                </div>
                            }
                        </InfoGroup>
                    </div>
                );
            })
        }
      </div>
    );
  }
};

export default TradfriView;