import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";

import MediaThumbnail from './../MediaThumbnail'

const MediaOverview = ({media, link}) => (

    <div className="media-overview">
      {
        media.map((media) => <Link key={media._id} to={link + media._id}><MediaThumbnail img={media.images.poster} title={media.title} /></Link>)
      }
    </div>
);

export default MediaOverview;