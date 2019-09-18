import React, { Component } from 'react';

class Button extends Component{
    constructor(props) {
        super(props);
        this.state = {pointer: false};
        this.SetPointer = this.SetPointer.bind(this);
        this.onClick = this.onClick.bind(this);
    }

    SetPointer(newState){
        if(this.props.enabled !== false)
            return;

        this.setState({pointer: newState});
    }

    onClick(e){
        if (!this.props.onClick)
            return;

        if(this.props.enabled !== false)
            this.props.onClick(e);
    }

    render(){
        return  <div className={"button " + (this.props.enabled === false ? "disabled ": "") + (this.state.pointer? "pointer-down": "")}
         onPointerEnter={() => this.SetPointer(true)}
            onPointerLeave={() =>  this.SetPointer(false)}
            onClick={this.onClick}>
            {this.props.text}
          </div>
    }
}

export default Button;