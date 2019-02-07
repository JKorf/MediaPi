import React, { Component } from 'react';
import { Link } from "react-router-dom";

import FooterLink from "./FooterLink.js";

import homeImage from "./../../Images/home.svg";
import entertainmentImage from "./../../Images/entertainment.svg";
import lightImage from "./../../Images/bulb.svg";
import settingsImage from "./../../Images/settings.svg";

const Footer = () => (
  <div className="footer">
    <FooterLink to="/" exact={true} img={homeImage} />
    <FooterLink to="/mediaplayer" img={entertainmentImage} />
    <FooterLink to="/light" img={lightImage} />
    <FooterLink to="/settings" img={settingsImage} />
  </div>
);

export default Footer;