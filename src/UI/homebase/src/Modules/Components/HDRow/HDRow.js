import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";
import SvgImage from "./../SvgImage"

const HDRow = ({img, text, clickHandler}) => (
    <div className="hd-row" onClick={clickHandler}>
        <div className="hd-row-image"><SvgImage src={img} /></div>
        <div className="hd-row-text truncate">{text}</div>
    </div>
);

export default HDRow;