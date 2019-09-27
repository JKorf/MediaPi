/*eslint no-loop-func: "off"*/
import React, { Component } from 'react';
import { Link } from "react-router-dom";
import axios from 'axios';

import { InfoGroup } from './../../Components/InfoGroup';
import SvgImage from './../../Components/SvgImage';
import Button from './../../Components/Button';
import SelectDevicesPopup from './../../Components/Popups/SelectDevicesPopup.js';

import tempImg from './../../../Images/thermometer.svg'
import lightingImg from './../../../Images/bulb.svg'
import switchImg from './../../../Images/switch.svg'
import settingsImg from './../../../Images/settings.svg'

class AutomationGroupView extends Component {
  constructor(props) {
    super(props);

    this.newGroup = this.props.match.params.id === "-1";

    this.props.functions.changeBack({ to: "/home/automation" });
    this.props.functions.changeTitle(this.newGroup ? "New group": "Edit group");
    this.props.functions.changeRightImage(null);

    this.state = {id: this.props.match.params.id, name: "", devices: []};
  }

  componentDidMount() {
     axios.get(window.vars.apiBase + 'home/get_devices').then(
        (data) => {
            this.setState({allDevices: data.data});

             if(!this.newGroup){
                axios.get(window.vars.apiBase + 'home/get_group?id=' + this.state.id).then(
                    (data) => {
                        console.log(data.data);
                        var devices = this.state.allDevices;
                        for (var i = 0; i < data.data.devices.length; i++){
                            devices.filter(d => d.id === data.data.devices[i].id)[0].selected = true;
                        }
                        this.setState({name: data.data.name, devices: data.data.devices, allDevices: devices});
                     },
                    (error) => { console.log(error) }
                );
            }
         },
        (error) => { console.log(error) }
      );
  }

  componentWillUnmount(){
  }

  getIcon(deviceType){
    if(deviceType === "Light")
        return lightingImg;

    if(deviceType === "Thermostat")
        return tempImg;

    if(deviceType === "Switch")
        return switchImg;
  }

  setSelectedDevices(devices)
  {
     this.setState({showSelectDevices: false, devices: devices});
  }

  save(){
    axios.post(window.vars.apiBase + 'home/save_group?'
        + 'id=' + this.state.id
        + '&name=' + encodeURIComponent(this.state.name)
        + '&devices=' + this.state.devices.filter(d => d.selected).map(d => d.id).join(','));
  }

  remove(){
    if(!window.confirm("Do you really want to remove group " + this.state.name + "?"))
        return false;

    axios.post(window.vars.apiBase + 'home/remove_group?id=' + this.state.id);
  }

  render() {
    return (
        <div className="automation-view">
            {this.state.showSelectDevices &&
                <SelectDevicesPopup devices={this.state.allDevices} onCancel={e => this.setState({showSelectDevices: false})} onSelect={e => this.setSelectedDevices(e)} />
            }

            <InfoGroup title="General">
                 <div className="automation-group-block">
                    <div className="automation-label">Name</div>
                    <div className="automation-value">
                        <input placeholder="Group name" value={this.state.name} onChange={e => this.setState({name: e.target.value})} />
                    </div>
                 </div>
            </InfoGroup>

            <div className="automation-devices">
                <InfoGroup title="Devices" configurable={true} configureIcon={settingsImg} onConfigure={e => this.setState({showSelectDevices: true})}>
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
                        </div>
                    )}
                    { this.state.devices.length === 0 && <div className="automation-no-devices">No devices</div>}
                </InfoGroup>
            </div>

            <div className="automation-group-save">
                <div className="automation-group-save-button"><Link to="/home/automation"><Button text="Save" onClick={e => this.save()} /></Link></div>
                <Link to="/home/automation"><Button text="Delete" onClick={e => this.remove()} /></Link>
            </div>
        </div>
    );
  }
};

export default AutomationGroupView;