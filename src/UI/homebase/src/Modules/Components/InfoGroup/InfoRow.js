import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";
import SvgImage from "./../SvgImage"

const InfoRow = ({name, value}) => (
    <div className="player-details-group-items label-row">
        <div className="label-field">{name}</div>
        <div className="label-value truncate">{value}</div>
    </div>
);

export default InfoRow;