import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";

import "./DashboardLink.css";

const DashboardLink = ({to, img, text}) => (
    <Link to={to}>
        <div className="dashboard-link">
            <div className="dashboard-link-icon">
                <img src={img} alt={text}/>
            </div>
            <div className="dashboard-link-text">{text}</div>
        </div>
    </Link>
);

export default DashboardLink;