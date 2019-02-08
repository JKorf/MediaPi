import React, { Component } from 'react';


class ColorIndicator extends Component {
  componentDidMount(){
  }

  componentWillUnmount(){
  }

  getColorString(type){
        if(!this.props.value)
            return;

        var a = this.props.value/100;
        if(type === 'grade')
            a = this.props.value / 10;


        var b = 120*a;
        return 'hsl('+b+',100%,35%)'
    }

  render() {
    var style = {
        color: this.getColorString()
    };

    return <span style={style}>{this.props.children}</span>
  }
}

export default ColorIndicator;