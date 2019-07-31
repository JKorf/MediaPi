import axios from 'axios';
import React, { Component } from 'react';
import Button from "./../Button"
import SvgImage from "./../SvgImage"

import failImage from "./../../../Images/fail.svg";
import successImage from "./../../../Images/success.svg";

import Popup from "./Popup.js"

class SystemHealthCheckPopup extends Component {
  constructor(props) {
    super(props);
    this.state = {loading: true};

    this.close = this.close.bind(this);
  }

  componentDidMount() {
      axios.post(window.vars.apiBase + 'util/system_health_check').then((data) =>{
        console.log(data);
        this.setState({loading: false, result: data.data});
      }, (error) => {
        this.setState({loading: false});
      });
  }

  componentWillUnmount() {
  }

  close()
  {
    this.props.onClose();
  }

  render() {
     const buttons = (
        <div>
        { !this.state.loading &&
            <Button classId="secondary" text="Close" onClick={this.close} />
         }
         </div>
    )

    return (
    <Popup title={this.state.loading ? "System health check in progress": "System health check results"} loading={this.state.loading} buttons={buttons} classId="health-check-popup">
         { this.state.result &&
          Object.keys(this.state.result).map((key) =>
                <div key={key} className="system-health-item">
                    <div className="system-health-key">{this.state.result[key].name}</div>
                    <div className="system-health-value"><SvgImage src={(this.state.result[key].result ? successImage: failImage)} /></div>
                    {!this.state.result[key].result && <div className="system-health-reason">{this.state.result[key].reason}</div> }
                </div>)
          }
     </Popup>
    )
  }
};
export default SystemHealthCheckPopup;
