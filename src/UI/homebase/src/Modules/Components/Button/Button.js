import React, { Component } from 'react';

const Button = ({text, onClick}) => (
  <div className="Button" onClick={onClick}>
        {text}
      </div>
);

export default Button;