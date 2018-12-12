import React, { Component } from 'react';
import MediaThumbnail from './../MediaThumbnail'

import './../media.css'

const MediaOverview = ({media}) => (

    <div className="media-overview">
      {
        media.map((media) => <MediaThumbnail key={media._id} img={media.images.poster} title={media.title} />)
      }
    </div>
);

export default MediaOverview;