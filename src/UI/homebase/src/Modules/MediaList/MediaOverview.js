import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";

import MediaThumbnail from './MediaThumbnail.js'

const MediaOverview = ({media, link}) => (

    <div className="media-overview">
      {
        media.map((media) =>
            <Link key={media.id} to={link + media.id}>
                <MediaThumbnail img={media.poster ? media.poster: media.images.poster} title={media.title} rating={media.rating} />
            </Link>)
      }
    </div>
);

export default MediaOverview;