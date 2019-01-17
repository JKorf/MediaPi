import React, { Component } from 'react';
import { Link } from "react-router-dom";

import SvgImage from "./../Components/SvgImage";

import backImage from "./../../Images/left.svg";

class Header extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    const backConfig = this.props.backConfig;
    const backButton = (
        <div className="header-back">
            <SvgImage src={backImage} />
        </div>
      );

      let link = <div />;
      if(backConfig.to)
        link = (<Link to={backConfig.to}>{backButton}</Link>)
      else if (backConfig.action)
        link = (<div onClick={backConfig.action}>{backButton}</div>)

    return (
        <div className="header">
        {link}
        <div className="title truncate">
            {this.props.title}
        </div>
        <div className="right-image">
            { this.props.rightImage &&
                <div onClick={this.props.rightImage.click}><SvgImage key={this.props.rightImage.image} src={this.props.rightImage.image}  /></div>
            }
        </div>
      </div>
    );
  }
};

export default Header;