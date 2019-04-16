import React, { Component } from 'react';
import { Link } from "react-router-dom";


class InfoMessage extends Component {
  constructor(props) {
    super(props);

    this.state = {startX: 0, xOffset: 0};

    this.done = this.done.bind(this);
    this.touchStart = this.touchStart.bind(this);
    this.touchMove = this.touchMove.bind(this);
    this.touchEnd = this.touchEnd.bind(this);
  }

  componentDidMount(){
    this.doneTimer = setTimeout(this.done, this.props.time);
  }

  componentWillUnmount(){
    clearTimeout(this.doneTimer);
  }

  done(){
    this.props.onDone();
  }

  touchStart(e){
    this.setState({startX: e.touches[0].clientX});
  }

   touchMove(e){
      console.log(e.changedTouches[0].clientX - this.state.startX);
      this.setState({xOffset: e.changedTouches[0].clientX - this.state.startX});
   }

  touchEnd(e){
    if(Math.abs(e.changedTouches[0].clientX - this.state.startX) > 100)
    {
        this.done();
        e.preventDefault();
    }else{
        this.setState({startX: 0, xOffset: 0});
    }
  }

  render() {
    var style = {};
    if(this.state.xOffset){
        style = {
            marginLeft: "calc(50% + " + this.state.xOffset + "px)",
        }
    }
    else{
        style ={
            transition: "margin-left 0.2s linear"
        }
    }

    return <div className="info-message" style={style} onTouchStart={this.touchStart} onTouchMove={this.touchMove} onTouchEnd={this.touchEnd}>
                { this.props.header && <div className={"info-message-header " + this.props.type}>{this.props.header}</div> }
                <Link to={this.props.linkTo} onClick={this.done}>
                <div className="info-message-text">{this.props.text}</div>
                { this.props.linkText && <div className="info-message-footer"><div className="info-message-link">{this.props.linkText}</div></div>  }
            </Link>
       </div>;

  }
}

export default InfoMessage;