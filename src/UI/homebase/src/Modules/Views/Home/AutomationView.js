import React, { Component } from 'react';
import { Link } from "react-router-dom";
import axios from 'axios';
import {withRouter} from 'react-router-dom'
import Socket from './../../../Socket2.js';

import { InfoGroup } from './../../Components/InfoGroup';
import Switch from './../../Components/Switch';
import SvgImage from './../../Components/SvgImage';
import Dragger from './../../Components/Dragger';

import tempImg from './../../../Images/thermometer.svg'
import lightingImg from './../../../Images/bulb.svg'
import switchImg from './../../../Images/switch.svg'
import addImg from './../../../Images/plus.svg'
import ikeaImg from './../../../Images/ikea.png'

class AutomationView extends Component {
  constructor(props) {
    super(props);

    this.props.functions.changeBack({ to: "/home/" });
    this.props.functions.changeTitle("Automation");
    this.props.functions.changeRightImage(null);

    this.state = {groups: [], devices: [], providers: [], showAddGroup: false};
    this.devicesUpdate = this.devicesUpdate.bind(this);
  }

  componentDidMount() {
      this.devicesSub = Socket.subscribe("devices", this.devicesUpdate);
  }

  componentWillUnmount(){
      Socket.unsubscribe(this.devicesSub);
  }

  devicesUpdate(subId, data){
    data.devices = data.devices.sort((a, b) => a.device_type === "Thermostat" ? -1 : 1);
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
      axios.post(window.vars.apiBase + 'home/set_group_state?group_id=' + group.id + "&state=" + value);
  }

  changeGroupDimmer(group, value)
  {
      console.log(value);
      group.dim = value;
      this.updateGroup(group);
      axios.post(window.vars.apiBase + 'home/set_group_dim?group_id=' + group.id + "&dim=" + value);
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

  getProviderIcon(providerType){
    if(providerType == "TradfriHub")
        return ikeaImg;
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

  resyncProvider(provider)
  {
    console.log("Resync " + provider.name);
    axios.post(window.vars.apiBase + 'home/resync_provider?name=' + encodeURIComponent(provider.name));

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
                        <Dragger value={group.dim} key={group.id} onDragged={e => this.changeGroupDimmer(group, e)}>
                            <div className="automation-group-name no-select"><Link to={"/home/automation-group/" + group.id}>{group.name}</Link></div>
                            <div className="automation-group-length no-select"><Link to={"/home/automation-group/" + group.id}>{group.devices.length}</Link></div>
                            <div className="automation-group-controls">
                                <Switch value={group.state} onToggle={e => this.toggleGroup(group, e)} />
                            </div>
                        </Dragger>
                    </div>
                )}
                { this.state.groups.length === 0 && <div className="automation-no-groups">No groups yet</div>}

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
                        <div className={"automation-device " + (!device.accessible? "inaccessible": "")} key={device.id}>
                            <div className="automation-device-type"><SvgImage src={this.getIcon(device.device_type)} /></div>
                            { device.device_type !== "Switch" && <Link to={"/home/automation-device/" + device.id}><div className="automation-device-name">{device.name}</div></Link> }
                            { device.device_type === "Switch" && <div className="automation-device-name">{device.name}</div> }
                            <div className="automation-device-template">{this.getDeviceChangeTemplate(device)}</div>
                        </div>
                    )}
                </InfoGroup>
            </div>

            <div className="automation-providers">
                <InfoGroup title="Providers">
                    <div className="automation-header">
                        <div className="automation-header-column automation-header-provider-type">type</div>
                        <div className="automation-header-column automation-header-name">name</div>
                        <div className="automation-header-column automation-header-action"></div>
                      </div>

                    { this.state.providers.map(provider =>
                        <div className={"automation-provider " + (!provider.accessible? "inaccessible": "")} key={provider.name}>
                            <div className="automation-provider-type"><div className="height-helper" /><img src={this.getProviderIcon(provider.type)} /></div>
                            <div className="automation-provider-name">{provider.name}</div>
                            <div className="automation-provider-resync" onClick={e => this.resyncProvider(provider)}>Resync</div>
                        </div>
                    )}
                </InfoGroup>
            </div>
        </div>
    );
  }
};

export default withRouter(AutomationView);