import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";
import SvgImage from "./../SvgImage";

const DashboardLink = ({to, img, text}) => (
    <Link to={to}>
        <div className="dashboard-link">
            <div className="dashboard-link-icon">
                <SvgImage src={img} alt={text}/>
            </div>
            <div className="dashboard-link-text">{text}</div>
        </div>
    </Link>
);

export default DashboardLink;