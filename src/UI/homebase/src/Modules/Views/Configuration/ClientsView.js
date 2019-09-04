import React, { Component } from 'react';
import axios from 'axios';
import ViewLoader from './../../Components/ViewLoader';
import { formatTime } from './../../../Utils/Util.js';
import { Link } from "react-router-dom";
import closeImg from './../../../Images/close.png'

class ClientsView extends Component {
  constructor(props) {
    super(props);

    this.state = {};

    this.props.functions.changeBack({to: "/configuration/"});
    this.props.functions.changeTitle("Access");
    this.props.functions.changeRightImage(null);
  }

  componentDidMount() {
    axios.get(window.vars.apiBase + 'access/clients').then(
        (data) => {
            this.setState({clients: data.data});
            console.log(data);
         },
        (error) => { console.log(error) }
    )
  }

  componentWillUnmount() {
  }

  revokeClient(client){
    if(window.confirm("Do you want to revoke access for client " + client.key + "?")){
        axios.post(window.vars.apiBase + "access/revoke_client?key=" + client.key);
        var clients = this.state.clients;
        clients.splice(clients.indexOf(client), 1);
        this.setState({clients: clients});
    }
  }

  render() {
    return <div className="access-view">
        <ViewLoader loading={!this.state.clients}/>
            { this.state.clients &&
                <div className="clients-list">
                { this.state.clients.map((client, index) => { return (
                    <div className="client-item" key={client.id}>
                        <Link to={"/configuration/clients/" + client.id} >
                            <div className="client-id truncate" >{client.key}</div>
                            <div className="client-issued">{formatTime(client.issued, true, true, true, true, true)}</div>
                            <div className="client-last-seen">{formatTime(client.last_seen, true, true, true, true, true)}</div>
                        </Link>

                        <div className="client-revoke"><img src={closeImg} alt="revoke client access" onClick={(e) => this.revokeClient(client)} /></div>
                    </div>
                    )})
                }
            </div>
            }
    </div>
  }
};

export default ClientsView;