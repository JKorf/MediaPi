import React, { Component } from 'react';
import axios from 'axios';
import Socket from './../../Socket.js';

import { InfoGroup } from './../Components/InfoGroup'
import ViewLoader from './../Components/ViewLoader';

class SettingsView extends Component {
  constructor(props) {
    super(props);

    this.state = { logFiles: [], loading: false, updateState: "Idle" };

    this.props.functions.changeBack({});
    this.props.functions.changeTitle("Settings");
    this.props.functions.changeRightImage(null);

    this.getLogFiles = this.getLogFiles.bind(this);
    this.updateUpdate = this.updateUpdate.bind(this);
  }

  componentDidMount() {
    this.getLogFiles();
  }

  componentWillUnmount() {
  }

  debugLogging(){
    axios.post(window.vars.apiBase + 'util/log')
  }

  getLogFiles(){
    axios.get(window.vars.apiBase + 'util/get_log_files').then((data) => {
        this.setState({logFiles: data.data});
    });
  }

  openLog(file)
  {
    this.setState({loading: true});
    axios.get(window.vars.apiBase + 'util/get_log_file?file=' + encodeURIComponent(file)).then((data) => {
        console.log(data);
        var html = data.data.replace(/\r\n/g, '<br />');
        var newWindow = window.open();
        newWindow.document.write(html);
        this.setState({loading: false});
    });
  }

  updateUpdate(id, data)
  {
    this.setState({updateState: data.state});
    if (data.completed)
    {
        if (data.error)
            alert("Update failed: " + data.error);
    }
  }

  checkUpdates()
  {
    this.setState({loading: true});
    axios.get(window.vars.apiBase + 'util/check_update').then((data) => {
        this.setState({loading: false});
        if(data.data.available)
        {
            if(window.confirm("New update available, download now?")){
                axios.post(window.vars.apiBase + 'util/update');
                this.updateSub = Socket.subscribe("1.update", this.updateUpdate);
            }
        }
    });
  }

  render() {
    return <div className="settings-view">
        <ViewLoader loading={this.state.loading || this.state.updateState != "Idle"} text={(this.state.updateState != "Idle" ? this.state.updateState: null)}/>
        <InfoGroup title="Appearance">
            Test
        </InfoGroup>

        <InfoGroup title="Log files">
            <div className="settings-log-files">
                { this.state.logFiles.map(file =>
                <div key={file[0]} className="settings-log" onClick={() => this.openLog(file[0])}>
                    <div className="settings-log-name">{file[0]}</div>
                    <div className="settings-log-size">{file[1]}</div>
                </div>) }
            </div>
        </InfoGroup>

        <input type="button" value="Debug logging" onClick={() => this.debugLogging()}/>
        <input type="button" value="Check for updates" onClick={() => this.checkUpdates()}/>

    </div>
  }
};

export default SettingsView;