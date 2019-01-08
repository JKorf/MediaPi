import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";
import SvgImage from "./../SvgImage"

const InfoGroup = ({title, children}) => (
    <div className="player-details-group">
        <div className="player-details-group-title">{title}</div>
        <div className="player-details-group-content">{children}</div>
    </div>
);

export default InfoGroup;