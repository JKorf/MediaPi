import React, { Component } from 'react';
import { NavLink } from "react-router-dom";

import SvgImage from "./../Components/SvgImage";

const FooterLink = ({to, img, exact}) => (
    <NavLink to={to} exact={exact} className="footer-link" activeClassName="selected">
        <SvgImage src={img} />
    </NavLink>
);

export default FooterLink;