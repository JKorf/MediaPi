import React, { Component } from 'react';
import { Link } from "react-router-dom";

import FooterLink from "./FooterLink.js";

import homeImage from "./../../Images/home.svg";
import mediaImage from "./../../Images/play.svg";
import lightImage from "./../../Images/bulb.svg";

const Footer = () => (
  <div className="footer">
    <FooterLink to="/" exact={true} img={homeImage} />
    <FooterLink to="/mediaplayer" img={mediaImage} />
    <FooterLink to="/light" img={lightImage} />
  </div>
);

export default Footer;