import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";
import Popup from "./../Popup"

const SelectPopup = ({title, show, children}) => (
    <Popup title={title} show={show}>
        {children}
        <div className="popup-buttons">
            Buttons
        </div>
    </Popup>
);

export default SelectPopup;