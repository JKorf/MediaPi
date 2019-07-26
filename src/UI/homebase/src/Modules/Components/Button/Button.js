import React, { Component } from 'react';

class Button extends Component{
    constructor(props) {
        super(props);
        this.state = {pointer: false};
        this.SetPointer = this.SetPointer.bind(this);
    }

    SetPointer(newState){
        this.setState({pointer: newState});
    }

    render(){
        return  <div className={"button " + (this.state.pointer? "pointer-down": "")}
         onPointerEnter={() => this.SetPointer(true)}
            onPointerLeave={() =>  this.SetPointer(false)}
            onClick={this.props.onClick}>
            {this.props.text}
          </div>
    }
}

export default Button;