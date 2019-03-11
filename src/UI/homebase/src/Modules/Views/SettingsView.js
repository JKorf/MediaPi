import React, { Component } from 'react';
import axios from 'axios';

import { InfoGroup } from './../Components/InfoGroup'
import ViewLoader from './../Components/ViewLoader';

class SettingsView extends Component {
  constructor(props) {
    super(props);

    this.state = { logFiles: [], loading: false };

    this.props.functions.changeBack({});
    this.props.functions.changeTitle("Settings");
    this.props.functions.changeRightImage(null);

    this.getLogFiles = this.getLogFiles.bind(this);
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

  checkUpdates()
  {
    this.setState({loading: true});
    axios.get(window.vars.apiBase + 'util/check_update').then((data) => {
        this.setState({loading: false});
        if(data.data.available)
        {
            if(window.confirm("New update available, download now?")){
                this.setState({loading: true});
                axios.post(window.vars.apiBase + 'util/update').then((data) => {
                    this.setState({loading: false});
                    alert("Successfully updated, going to restart to complete update");
                },(err) =>{
                    this.setState({loading: false});
                    alert("Update failed: " + err.response.data);
                });
            }
        }
    });
  }

  render() {
    return <div className="settings-view">
        <ViewLoader loading={this.state.loading}/>
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