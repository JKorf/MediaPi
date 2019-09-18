import React, { Component } from 'react';
import Popup from "./Popup.js"
import Button from "./../Button"
import CheckBox from "./../CheckBox"
import SvgImage from "./../SvgImage"

import tempImg from './../../../Images/thermometer.svg'
import lightingImg from './../../../Images/bulb.svg'
import switchImg from './../../../Images/switch.svg'

class SelectDevicesPopup extends Component {
  constructor(props) {
    super(props);

    this.state = {devices: this.props.devices};
    this.cancel = this.cancel.bind(this);
    this.select = this.select.bind(this);
  }

  cancel()
  {
    this.props.onCancel();
  }

  select()
  {
    this.props.onSelect(this.state.devices.filter(d => d.selected));
  }

  toggleDevice(device, value){
    device.selected = value;
    this.updateDevice(device);
  }

  updateDevice(device)
  {
      var currentDevices = this.state.devices;
      var index = currentDevices.indexOf(device);
      currentDevices.splice(index, 1);
      currentDevices.splice(index, 0, device);
      this.setState({devices: currentDevices});
  }

  getIcon(deviceType){
    if(deviceType === "Light")
        return lightingImg;

    if(deviceType === "Thermostat")
        return tempImg;

    if(deviceType === "Switch")
        return switchImg;
  }

  render() {
    const buttons = (
        <div>
         <Button classId="secondary" text="Cancel" onClick={this.cancel} />
         <Button classId="secondary" text="Select"  onClick={this.select} />
         </div>
    )
    return (
    <Popup title="Select devices" loading={false} buttons={buttons}>
        <div className="automation-group-devices-select">
            { this.props.devices.filter(d => d.device_type === "Switch" || d.device_type === "Light").map(device =>
                <div className="automation-device" key={device.id}>
                        <div className="automation-device-select-type"><SvgImage src={this.getIcon(device.device_type)} /></div>
                        <div className="automation-device-select-name" onClick={e => this.toggleDevice(device, e)}>{device.name}</div>
                        <div className="automation-device-select-checkbox"><CheckBox value={device.selected} onChange={e => this.toggleDevice(device, e)} /></div>
                    </div>

//                <div className="automation-group-device-select-item" key={device.id}>
//                    <div className="automation-group-device-select-name">{device.name}</div>
//                    <div className="automation-group-device-select-check"><CheckBox value={device.selected} onChange={e => this.toggleDevice(device, e)} /></div>
//                </div>
            )}
        </div>
    </Popup>
    )
  }
};
export default SelectDevicesPopup;
