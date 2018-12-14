import React, { Component } from 'react';

const Button = ({text, onClick}) => (
  <div className="button" onClick={onClick}>
        {text}
      </div>
);

export default Button;