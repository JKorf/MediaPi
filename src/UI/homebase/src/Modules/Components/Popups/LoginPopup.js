/*eslint no-mixed-operators: "off"*/

import React, { Component } from 'react';
import Popup from "./Popup.js"
import Button from "./../Button"
import axios from 'axios';
import Socket2 from './../../../Socket2.js'

class LoginPopup extends Component {
  constructor(props) {
    super(props);

    this.state = {pw: "", loading: false, authError: "", refreshing: false};

    this.login = this.login.bind(this);
    this.setSessionKey = this.setSessionKey.bind(this);
    this.processAuthResult = this.processAuthResult.bind(this);
  }

  componentWillMount(){
    var clientId = localStorage.getItem('Client-ID');
    if (!clientId){
        // No client id yet, new client
        clientId = this.generate_id();
        localStorage.setItem('Client-ID', clientId);
        axios.defaults.headers.common['Client-ID'] = clientId;
        this.setState({loading: false});
    }
    else{
        // Have a client id, try to refresh
        this.setState({refreshing: true});
        axios.defaults.headers.common['Client-ID'] = clientId;
        axios.post(window.vars.apiBase + "auth/refresh").then(this.processAuthResult, this.processAuthResult);
    }
  }

  login()
  {
    this.setState({loading: true});
    axios.post(window.vars.apiBase + "auth/login?p=" + encodeURIComponent(this.state.pw)).then(this.processAuthResult, this.processAuthResult);
  }

  generate_id()
  {
      return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
        (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
      )
  }

  processAuthResult(result)
  {
    if (result.response)
        result = result.response;

    if(!result.status)
    {
        this.setState({authError: "No connection could be made to server"});
    }
    else if(result.status === 200)
    {
        console.log("Successfully authorized");
        this.setSessionKey(result.data.key);
        return;
    }
    else if(result.status === 401)
    {
        console.log("Authorization failed, need to log in again");
        if(this.state.refreshing)
            this.setState({refreshing: false});
        else
            this.setState({authError: "Authorization failed"});
    }
    else
    {
        this.setState({authError: "Error during authentication: " + result.statusText});
    }
    this.setState({loading: false});
  }

  setSessionKey(key){
    sessionStorage.setItem('Session-Key', key);
    Socket2.connect();
    this.props.onAuthorize();
  }

  render() {
    const buttons = (
        <div>
         <Button classId="secondary" text="Login" enabled={!this.state.loading} onClick={this.login} />
         </div>
    )
    return (
    <Popup title="Login" buttons={buttons}>
        <div className="login-content">
            <div className="login-input"><input type="password" onKeyPress={(e) => { if (e.key === "Enter") this.login(); }} value={this.state.pw} onChange={(e) => this.setState({pw:e.target.value})} placeholder="password"/></div>
            <div className="login-error">{this.state.authError}</div>
        </div>
    </Popup>
    )
  }
};
export default LoginPopup;
