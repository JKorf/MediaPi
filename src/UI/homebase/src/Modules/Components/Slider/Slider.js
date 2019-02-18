import React, { Component } from 'react';

import SvgImage from './../SvgImage/';

class Slider extends Component {
  constructor(props) {
    super(props);
    this.state = {showToolTip: false, startX: 0, currentX: 0};

    this.elementRef = React.createRef();

    this.touchStart = this.touchStart.bind(this);
    this.touchEnd = this.touchEnd.bind(this);
    this.touchMove = this.touchMove.bind(this);
    this.touchStartBackground = this.touchStartBackground.bind(this);
  }

  touchStart(e){
    this.beforeChange = this.props.value;
    this.setState({showToolTip: true, startX: e.touches[0].clientX, currentX: e.touches[0].clientX});
  }

  touchStartBackground(e){
    var touchPosition = e.touches[0].clientX;
    var thumbPosition = this.elementRef.current.getElementsByClassName("slider-thumb")[0].getBoundingClientRect().left + 5;
    this.setState({showToolTip: true, startX: thumbPosition, currentX: touchPosition});
  }

  touchMove(e){
    if(!this.state.showToolTip)
        return;

    this.setState({currentX: e.touches[0].clientX})
  }

  touchEnd(){
    this.setState({showToolTip: false, startX: 0, currentX: 0});
    if (this.beforeChange != this.newValue)
        this.props.onChange(this.newValue);
  }

  render() {
    const min = this.props.min;
    const max = this.props.max;
    const value = this.props.value;
    const percentage = ((value - min) / (max - min)) * 100;
    let offset = this.state.startX - this.state.currentX;
    let width = 0;
    if (this.elementRef.current){
        width = this.elementRef.current.getElementsByClassName("slider-background")[0].offsetWidth;
    }

    const percentPixels = width * (percentage / 100);
    if (percentPixels - offset < 0)
        offset = percentPixels;
    if (percentPixels - offset > width)
        offset = -width + percentPixels;

    const left = percentage / 100 * width - offset;
    const leftPercentage = left / width;
    this.newValue = (max - min) * leftPercentage + min;

    let minStr = min;
    let maxStr = max;
    let valueStr = value;
    let newValueStr = this.newValue;
    if(this.props.format){
        if (this.props.formatMinMax) minStr = this.props.formatMinMax(minStr);
        else minStr = this.props.format(minStr);
        if (this.props.formatMinMax) maxStr = this.props.formatMinMax(maxStr);
        else maxStr = this.props.format(maxStr);

        valueStr = this.props.format(valueStr);
        newValueStr = this.props.format(newValueStr);
    }

    const toolTipStyle = {
      left: left + "px",
      display: this.state.showToolTip ? "block": "none",
    };

    let thumbStyle = {
        left: "calc(" + percentage + "% - 5px)"
    };
    if(this.state.showToolTip)
        thumbStyle.left = left - 5 + "px";

    let iconClass= "";
    if(this.props.iconLeft && this.props.iconRight)
        iconClass = "icon-both";
    else if(this.props.iconLeft)
        iconClass = "icon-left";
    else if(this.props.iconRight)
        iconClass = "icon-right";

    return (
        <div ref={this.elementRef} className="slider">
            { this.props.iconLeft &&
                <div className="slider-icon-left"><SvgImage src={this.props.iconLeft} /></div>
            }
            { this.props.iconRight &&
                <div className="slider-icon-right"><SvgImage src={this.props.iconRight} /></div>
            }
            <div className={"slider-content " + iconClass}>
                <div className="slider-tooltip" style={toolTipStyle}>{newValueStr}</div>
                <div className="slider-info">
                    <div className="slider-value">{(this.props.leftValue == "value" ? valueStr: minStr)}</div>
                    <div className="slider-max">{maxStr}</div>
                </div>
                <div className="slider-background" onTouchStart={this.touchStartBackground} onTouchMove={this.touchMove} onTouchEnd={this.touchEnd}></div>
                <div className="slider-thumb" style={thumbStyle} onTouchMove={this.touchMove} onTouchStart={this.touchStart} onTouchEnd={this.touchEnd}></div>

            </div>
        </div>
    )
  }
}

export default Slider;