import React, { Component } from 'react';
import { Link } from "react-router-dom";

const App = ({name, age}) => (
  <div className="header">
        <Link to="/">home</Link>
        <Link to="/shows">shows</Link>
      </div>
);

export default App;