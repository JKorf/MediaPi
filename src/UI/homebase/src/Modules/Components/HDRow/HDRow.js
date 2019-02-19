import React from 'react';
import SvgImage from "./../SvgImage"
import seenImage from './../../../Images/watched.svg';

const HDRow = ({img, text, seen, clickHandler}) => (
    <div className="hd-row" onClick={clickHandler}>
        <div className="hd-row-image"><SvgImage src={img} /></div>
        <div className={"hd-row-text truncate2 " + (seen?"seen":"") } >{text}</div>
        { seen && <div className="hd-row-seen"><SvgImage src={seenImage} /></div> }
    </div>
);

export default HDRow;