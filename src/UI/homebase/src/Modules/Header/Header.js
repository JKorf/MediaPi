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

      let link;
      if(backConfig.to)
        link = (<Link to={backConfig.to}>{backButton}</Link>)
      else
        link = (<div onClick={backConfig.action}>{backButton}</div>)

    return (
        <div className="header">
        {link}
      </div>
    );
  }
};

export default Header;