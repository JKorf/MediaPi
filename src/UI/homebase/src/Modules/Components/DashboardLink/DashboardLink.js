import React, { Component } from 'react';
import { Link } from "react-router-dom";
import SvgImage from "./../SvgImage";

class DashboardLink extends Component{
    constructor(props) {
        super(props);
        this.state = {pointer: false};
        this.SetPointer = this.SetPointer.bind(this);
    }

    SetPointer(newState){
        this.setState({pointer: newState});
    }

    render(){
        return <Link to={this.props.to}>
            <div className={"dashboard-link " + (this.state.pointer? "pointer-down": "")}
            onPointerEnter={() => this.SetPointer(true)}
            onPointerLeave={() =>  this.SetPointer(false)}>
                <div className="dashboard-link-icon">
                    <SvgImage src={this.props.img} alt={this.props.text}/>
                </div>
                <div className="dashboard-link-text">{this.props.text}</div>
            </div>
        </Link>
    }
}

export default DashboardLink;