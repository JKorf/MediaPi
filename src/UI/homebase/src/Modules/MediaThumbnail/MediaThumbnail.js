import React, { Component } from 'react';

const MediaThumbnail = ({img, title}) => (
  <div className="media-thumbnail">
        <img className="media-thumbnail-img" src={img} />
        <div className="media-thumbnail-title">{title}</div>
      </div>
);

export default MediaThumbnail;