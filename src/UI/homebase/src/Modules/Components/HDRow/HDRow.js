import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";
import SvgImage from "./../SvgImage"

const HDRow = ({img, text}) => (
    <div className="hd-row">
        <div className="hd-row-image"><SvgImage src={img} /></div>
        <div className="hd-row-text">{text}</div>
    </div>
);

export default HDRow;