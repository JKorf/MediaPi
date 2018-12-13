import React, { Component } from 'react';
import { Link } from "react-router-dom";

const Header = () => (
  <div className="header">
        <Link to="/">Home</Link> | <Link to="/mediaplayer">Mediaplayer</Link>
      </div>
);

export default Header;