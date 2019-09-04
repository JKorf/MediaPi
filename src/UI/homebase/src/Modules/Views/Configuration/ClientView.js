import React, { Component } from 'react';
import axios from 'axios';
import ViewLoader from './../../Components/ViewLoader';
import CheckBox from './../../Components/CheckBox';
import { formatTime } from './../../../Utils/Util.js';

class ClientView extends Component {
  constructor(props) {
    super(props);

    this.state = {};

    this.props.functions.changeBack({to: "/configuration/clients/"});
    this.props.functions.changeTitle("Access log");
    this.props.functions.changeRightImage(null);
  }

  componentDidMount() {
    axios.get(window.vars.apiBase + 'access/client?id=' + this.props.match.params.id).then(
        (data) => {
            this.setState({entries: data.data});
            console.log(data);
         },
        (error) => { console.log(error) }
    )
  }

  componentWillUnmount() {
  }

  render() {
    return <div className="access-view">
        <ViewLoader loading={!this.state.entries}/>
            { this.state.entries &&
                <div className="client-list">
                { this.state.entries.map((client, index) => { return (
                    <div className="client-access" key={client.id}>
                        <div className="client-ip" >{client.ip}</div>
                        <div className="client-platform" >{client.platform} {client.browser}</div>
                        <div className="client-timestamp" >{formatTime(client.timestamp, true, true, true, true, true)}</div>
                        <div className="client-type">{client.type}</div>
                        <div className="client-success"><CheckBox readonly={true} value={client.success === 1} /></div>
                    </div>
                    )})
                }
            </div>
            }
    </div>
  }
};

export default ClientView;