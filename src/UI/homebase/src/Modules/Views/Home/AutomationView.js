import React, { Component } from 'react';
import { Link } from "react-router-dom";
import axios from 'axios';
import {withRouter} from 'react-router-dom'
import Socket from './../../../Socket2.js';

import { InfoGroup } from './../../Components/InfoGroup';
import Switch from './../../Components/Switch';
import SvgImage from './../../Components/SvgImage';
import Button from './../../Components/Button';

import tempImg from './../../../Images/thermometer.svg'
import lightingImg from './../../../Images/bulb.svg'
import switchImg from './../../../Images/switch.svg'
import addImg from './../../../Images/plus.svg'

class AutomationView extends Component {
  constructor(props) {
    super(props);

    this.props.functions.changeBack({ to: "/home/" });
    this.props.functions.changeTitle("Automation");
    this.props.functions.changeRightImage(null);

    this.state = {groups: [], devices: [], showAddGroup: false};
    this.devicesUpdate = this.devicesUpdate.bind(this);
  }

  componentDidMount() {
//    axios.get(window.vars.apiBase + 'home/get_overview').then(
//        (data) => {
//            console.log(data.data);
//            this.setState({groups: data.data[0], devices: data.data[1]});
//         },
//        (error) => { console.log(error) }
//    )

      this.devicesSub = Socket.subscribe("devices", this.devicesUpdate);
  }

  componentWillUnmount(){
      Socket.unsubscribe(this.devicesSub);
  }

  devicesUpdate(subId, data){
    this.setState(data);
  }

  toggleSwitch(device, value){
      console.log(value);
      device.active = value;
      this.updateDevice(device);
      axios.post(window.vars.apiBase + 'home/set_switch?device_id=' + device.id + "&state=" + value);
  }

  toggleLight(device, value){
      console.log(value);
      device.on = value;
      this.updateDevice(device);
      axios.post(window.vars.apiBase + 'home/set_light_state?device_id=' + device.id + "&state=" + value);
  }

  toggleGroup(group, value)
  {
      console.log(value);
      group.state = value;
      this.updateGroup(group);
      axios.post(window.vars.apiBase + 'home/set_group?group_id=' + group.id + "&state=" + value);
  }

  changeTemperature(device, value){
       device.setpoint = value;
       this.updateDevice(device);

        if (this.timer)
            clearTimeout(this.timer);
        this.timer = setTimeout(() => {
            axios.post(window.vars.apiBase + 'home/set_setpoint?device_id=ToonThermostat&temperature=' + device.setpoint).then(
                (data) => {
                    console.log(data);
                 },
                (error) => { console.log(error) }
            )
        }, 750);
  }

  updateDevice(device)
  {
      var currentDevices = this.state.devices;
      var index = currentDevices.indexOf(device);
      currentDevices.splice(index, 1);
      currentDevices.splice(index, 0, device);
      this.setState({devices: currentDevices});
  }

  updateGroup(group)
  {
      var currentGroups = this.state.groups;
      var index = currentGroups.indexOf(group);
      currentGroups.splice(index, 1);
      currentGroups.splice(index, 0, group);
      this.setState({groups: currentGroups});
  }

  getDeviceChangeTemplate(device)
  {
    if(device.device_type === "Thermostat")
        return <div className="automation-thermostat-template">
            <div className="temp-widget-decrease-temp" onClick={() => this.changeTemperature(device, device.setpoint - 1)}>-</div>
            <div className="temp-widget-current-setpoint">{device.setpoint + "°C"}</div>
            <div className="temp-widget-increase-temp" onClick={() => this.changeTemperature(device, device.setpoint + 1)}>+</div>
        </div>
    if(device.device_type === "Switch")
        return <Switch value={device.active} onToggle={e => this.toggleSwitch(device, e)} />
    if(device.device_type === "Light")
        return <Switch value={device.on} onToggle={e => this.toggleLight(device, e)} />
  }

  getIcon(deviceType){
    if(deviceType === "Light")
        return lightingImg;

    if(deviceType === "Thermostat")
        return tempImg;

    if(deviceType === "Switch")
        return switchImg;
  }

  createGroup(name)
  {
    this.setState({showAddGroup: false});
    console.log("Create " + name);
    axios.post(window.vars.apiBase + 'home/add_group?name=' + encodeURIComponent(name)).then(
        (data) => {
            console.log(data.data);
            var groups = this.state.groups;
            groups.push({ id: data.data, name: name, devices: [] });
            this.setState({groups: groups});
         },
        (error) => { console.log(error) }
    )
  }

  removeGroup(group)
  {
    if(window.confirm("Do you really want to remove group " + group.name + "?")){
        axios.post(window.vars.apiBase + 'home/remove_group?id=' + group.id);
        var groups = this.state.groups;
        groups.splice(groups.indexOf(group));
        this.setState({groups: groups});
    }
  }

  render() {

    return (
        <div className="automation-view">
            <InfoGroup title="Groups" configurable={true} configureIcon={addImg} onConfigure={e => this.props.history.push('/home/automation-group/-1')}>
                <div className="automation-header">
                    <div className="automation-header-column automation-header-group-name">name</div>
                    <div className="automation-header-column automation-header-length">devices</div>
                    <div className="automation-header-column"></div>
                  </div>
                { this.state.groups.map(group =>
                    <div className="automation-group" key={group.id}>
                        <div className="automation-group-name"><Link to={"/home/automation-group/" + group.id}>{group.name}</Link></div>
                        <div className="automation-group-length"><Link to={"/home/automation-group/" + group.id}>{group.devices.length}</Link></div>
                        <div className="automation-group-controls">
                            <Switch value={group.state} onToggle={e => this.toggleGroup(group, e)} />
                        </div>
                    </div>
                )}
                { this.state.groups.length == 0 && <div className="automation-no-groups">No groups yet</div>}

            </InfoGroup>

            <div className="automation-devices">
                <InfoGroup title="Devices">
                    <div className="automation-header">
                        <div className="automation-header-column automation-header-type">type</div>
                        <div className="automation-header-column automation-header-name">name</div>
                        <div className="automation-header-column automation-header-action"></div>
                        <div className="automation-header-column"></div>
                      </div>

                    { this.state.devices.map(device =>
                        <div className="automation-device" key={device.id}>
                            <div className="automation-device-type"><SvgImage src={this.getIcon(device.device_type)} /></div>
                            <div className="automation-device-name">{device.name}</div>
                            <div className="automation-device-template">{this.getDeviceChangeTemplate(device)}</div>
                        </div>
                    )}
                </InfoGroup>
            </div>
        </div>
    );
  }
};

export default withRouter(AutomationView);