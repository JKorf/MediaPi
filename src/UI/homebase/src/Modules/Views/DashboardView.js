import React, { Component } from 'react';
import axios from 'axios'

import View from './View.js'
import SvgImage from './../Components/SvgImage'
import TestWidget from './../Widgets/TestWidget.js'
import MediaPlayerWidget from './../Widgets/MediaPlayerWidget.js'
import Socket from './../../Socket.js'

import settingsImage from './../../Images/settings.svg';

class DashboardView extends Component {
  constructor(props) {
    super(props);
    this.props.functions.changeBack({});
    this.props.functions.changeTitle("Home base");
    this.props.functions.changeRightImage({image: settingsImage, click: this.toggleEditMode});

    this.resizeUpdate = this.resizeUpdate.bind(this);

    this.dashboardRef = React.createRef();
    this.maxColumns = 8;
  }

  componentDidMount() {
      window.addEventListener("resize", this.resizeUpdate);
  }

  componentWillUnmount() {
    window.removeEventListener('resize', this.resizeUpdate)
  }

  resizeUpdate(){
    this.forceUpdate();
  }

  toggleEditMode()
  {
    console.log("Edit!");
  }

  render() {
    var layout = {
         media: { x: 0, y: 0, width: 8, height: 4},
         test1: { x: 0, y: 4, width: 4, height: 2},
         test2: { x: 4, y: 4, width: 4, height: 2},
    };

    if(this.dashboardRef.current)
    {
        var width = this.dashboardRef.current.clientWidth;
        if(width > 400)
        {
            layout = {
                media: { x: 0, y: 0, width: 4, height: 3},
                test1: { x: 4, y: 0, width: 4, height: 2},
                test2: { x: 4, y: 2, width: 4, height: 2},
            };
        }
        if(width > 600)
        {
            layout = {
                media: { x: 0, y: 0, width: 4, height: 2},
                test1: { x: 4, y: 0, width: 2, height: 2},
                test2: { x: 6, y: 0, width: 2, height: 2},
            };
        }
    }
    return (<div className="dashboard" ref={this.dashboardRef}>
              <div className="dashboard-edit"><SvgImage src={settingsImage} /></div>
              <TestWidget dashboard={this.dashboardRef} {...layout.test1}/>
              <TestWidget dashboard={this.dashboardRef} {...layout.test2}/>
              <MediaPlayerWidget title="players" dashboard={this.dashboardRef} {...layout.media} />
            </div>);

  }
};

export default DashboardView;