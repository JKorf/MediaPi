import React from 'react';

const Button = ({text, onClick, classId}) => (
  <div className={"button " + classId} onClick={onClick}>
        {text}
      </div>
);

export default Button;