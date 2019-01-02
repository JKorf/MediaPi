import React, { Component } from 'react';

const MediaThumbnail = ({img, title, rating}) => (
  <div className="media-thumbnail">
        <img className="media-thumbnail-img" src={img} />
        <div className="media-thumbnail-info">
            <div className="media-thumbnail-info-title  truncate2">{title}</div>
            <div className="media-thumbnail-info-rating">{rating}</div>
        </div>
      </div>
);

export default MediaThumbnail;