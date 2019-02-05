import React, { Component } from 'react';
import ReactDOM from 'react-dom';

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


    this.widgetRefs = [
        {
            component: <MediaPlayerWidget ref={React.createRef()} title="players" updateFunc={() => this.resizeUpdate()}/>,
            style: {},
            width: 0,
            height: 0,
            x: -1,
            y: -1,
            index: 1
        },
        {
            component: <TestWidget ref={React.createRef()} />,
            style: {},
            width: 0,
            height: 0,
            x: -1,
            y: -1,
            index: 2
        },
        {
            component: <TestWidget ref={React.createRef()} />,
            style: {},
            width: 0,
            height: 0,
            x: -1,
            y: -1,
            index: 3
        },
        {
            component: <TestWidget ref={React.createRef()} />,
            style: {},
            width: 0,
            height: 0,
            x: -1,
            y: -1,
            index: 4
        },
        {
            component: <TestWidget ref={React.createRef()} />,
            style: {},
            width: 0,
            height: 0,
            x: -1,
            y: -1,
            index: 5
        }
    ];

    for(var i = 0; i < this.widgetRefs.length; i++)
        this.widgetRefs[i].ref = this.widgetRefs[i].component.ref;

    this.resizeUpdate = this.resizeUpdate.bind(this);
    this.findFreeSpot = this.findFreeSpot.bind(this);
    this.initDashboard = this.initDashboard.bind(this);
    this.getWidgetsInArea = this.getWidgetsInArea.bind(this);

    this.dashboardRef = React.createRef();
    this.maxColumns = 8;
  }

  componentDidMount() {
      window.addEventListener("resize", this.resizeUpdate);

      this.initDashboard(false);
  }

  componentWillUnmount() {
    window.removeEventListener('resize', this.resizeUpdate)
  }

  resizeUpdate(){
    // Reset the dashboard and let the widget take their original size
    this.initDashboard(true);
    this.forceUpdate();

    // Recalculate the widget position/size
//    this.initDashboard(false);
//    this.forceUpdate();
  }

  toggleEditMode()
  {
    console.log("Edit!");
  }

  findFreeSpot(width, height){
    for(var y = 0; y < 20; y++){
        for(var x = 0; x < 8 - width; x++){
            var result = this.getWidgetsInArea(x, y, width, height);
            if (result.length == 0)
                return {x: x, y: y};
        }
     }

     return null;
  }

  isFree(x, y)
  {
    for(var i = 0; i < this.widgetRefs.length; i++){
        var widget = this.widgetRefs[i];
        if(widget.x != -1){
            if (x >= widget.x && x < widget.x + widget.width
            && y >= widget.y && y < widget.y + widget.height)
                return false;
        }
    }

    return true;
  }

  getWidgetsInArea(x, y, width, height){
    var result = [];
    for(var j = 0; j < height; j++){
        for(var i = 0; i < width; i++){
            var checkX = x + i;
            var checkY = y + y;

            for(var k = 0; k < this.widgetRefs.length; k++){
                var widget = this.widgetRefs[k];
                if(result.indexOf(widget) != -1)
                    continue;

                if(widget.x != -1){
                    if (checkX >= widget.x && checkX < widget.x + widget.width
                    && checkY >= widget.y && checkY < widget.y + widget.height)
                        result.push(widget);
                }
            }
        }
    }
    return result;
  }

  initDashboard(reset){

    if(this.dashboardRef.current)
    {
//        if(reset)
//        {
//            for(var i = 0; i < this.widgetRefs.length; i++)
//            {
//                this.widgetRefs[i].x = -1;
//                this.widgetRefs[i].y = -1;
//                this.widgetRefs[i].style = {};
//                this.widgetRefs[i].width = 0;
//                this.widgetRefs[i].height = 0;
//            }
//        }
//        else
//        {
            const dashboardWidth = this.dashboardRef.current.clientWidth;
            const columnWidth = dashboardWidth / 8;

            for(var i = 0; i < this.widgetRefs.length; i++){
                var widget = this.widgetRefs[i];
                var minSize = widget.ref.current.getSize();

                console.log("Prefered size: ", minSize);

//                var node = ReactDOM.findDOMNode(widget.ref.current);
//                if (!node)
//                    continue;
//
//                const thisWidth = node.parentElement.clientWidth;
//                const thisHeight = node.parentElement.clientHeight;
//
//                const columns =  Math.min(Math.ceil(thisWidth / columnWidth), 8);
//                const rows = Math.ceil(thisHeight / columnWidth);
//
//                widget.width = columns;
//                widget.height = rows;
//                widget.style = {
//                    width: 0,
//                    height: 0,
//                    left: 0,
//                    top: 0
//                };
            }
            return;

//            for(var i = 0; i < this.widgetRefs.length; i++){
//                var widget = this.widgetRefs[i];
//                var pos = this.findFreeSpot(widget.width, widget.height);
//                widget.x = pos.x;
//                widget.y = pos.y;
//            }
//
//            for(var i = 0; i < this.widgetRefs.length; i++){
//                var widget = this.widgetRefs[i];
//                widget.style.left = (widget.x * columnWidth) + "px";
//                widget.style.width = (widget.width * columnWidth) + "px";
//                widget.style.top = (widget.y * columnWidth) + "px";
//                widget.style.height = (widget.height * columnWidth) + "px";
//            }
//        }
        this.forceUpdate();
     }
  }

  render() {
    return (<div className="dashboard" ref={this.dashboardRef}>
            { this.widgetRefs.map(widget => <div className="widget-wrap" key={widget.index} style={widget.style}>{widget.component}</div>) }
            </div>);
  }
};

export default DashboardView;