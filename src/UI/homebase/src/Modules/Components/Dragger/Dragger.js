import React, { Component } from 'react';
import { Link } from "react-router-dom";
import SvgImage from "./../SvgImage";

class Dragger extends Component{
    constructor(props) {
        super(props);
        this.down = false;
        this.changing = false;
        this.state = {width: 0, showToolTip: false, newPercentage: this.props.value};
        this.startX = 0;
        this.wrapperRef = React.createRef();

        this.CalculateNewPercentage = this.CalculateNewPercentage.bind(this);
    }

    PointerDown(e){
        this.down = true;
        this.startX = e.pageX;
    }

    PointerMove(e){
        if(this.down){
            this.currentX = e.pageX;
            var delta = this.currentX - this.startX;
            if(delta < 15 && delta > -15 && !this.changing){
                return;
            }
            this.changing = true;
            var newValue = this.CalculateNewPercentage(delta);
            this.SetBackground(newValue);
            this.setState({newPercentage: newValue, showToolTip: true });
        }
    }

    componentDidMount(){
        this.SetBackground(this.props.value);
    }

    componentDidUpdate(prev){
        if(prev.value != this.props.value)
            this.SetBackground(this.props.value);
    }

    PointerUp(){
        this.down = false;
        if(!this.changing)
            return;

        this.changing = false;
        var delta = this.currentX - this.startX;

        var newValue = this.CalculateNewPercentage(delta);
        console.log("Up at delta " + delta + ", " + newValue + "%");
        this.props.onDragged(newValue);


        this.setState({showToolTip: false});
    }

    CalculateNewPercentage(delta){
        var totalWidth = this.wrapperRef.current.clientWidth;
        var percentage = Math.round(delta / totalWidth * 100);
        var newValue = this.props.value + percentage;
        if (newValue > 100) newValue = 100;
        if (newValue < 0) newValue = 0;
        return newValue;
    }

    SetBackground(value){
        var width = value / 100 * this.wrapperRef.current.clientWidth;
        this.setState({percentageWidth : width});
    }

    render(){
        return <div className="dragger-wrapper" ref={this.wrapperRef}>
            <div className="dragger-background" style={{width: this.state.percentageWidth + "px"}}></div>
             <div className="dragger-content" onPointerCancel={(e) => this.PointerUp()} onPointerDown={(e) => this.PointerDown(e)} onPointerUp={(e) => this.PointerUp()} onPointerMove={(e) => this.PointerMove(e)}>
                {this.props.children}
            </div>
            { this.state.showToolTip &&
                <div className={"dragger-tooltip " + (this.state.newPercentage > 50? "left": "right")}>{this.state.newPercentage}%</div>
            }
        </div>
    }
}

export default Dragger;