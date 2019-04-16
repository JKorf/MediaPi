import React, { Component } from 'react';

import FavoriteSeriesWidget from './../Widgets/FavoriteSeriesWidget.js'
import TempWidget from './../Widgets/TempWidget.js'
import LightWidget from './../Widgets/LightWidget.js'

class DashboardView extends Component {
  constructor(props) {
    super(props);
    this.props.functions.changeBack({});
    this.props.functions.changeTitle("Home base");
    this.props.functions.changeRightImage(null);


    this.widgetRefs = [
        {
            component: <LightWidget title="Lights" titleLink={"/home/lighting"} ref={React.createRef()} />,
            style: {},
            width: 0,
            height: 0,
            x: -1,
            y: -1,
            index: 0
        },
        {
            component: <TempWidget title="Temperature" titleLink={"/home/heating"} ref={React.createRef()} />,
            style: {},
            width: 0,
            height: 0,
            x: -1,
            y: -1,
            index: 1
        },
        {
            component: <FavoriteSeriesWidget title="favorites" ref={React.createRef()} />,
            style: {},
            width: 0,
            height: 0,
            x: -1,
            y: -1,
            index: 2
        }
    ];

    for(var i = 0; i < this.widgetRefs.length; i++)
        this.widgetRefs[i].ref = this.widgetRefs[i].component.ref;

    this.resizeUpdate = this.resizeUpdate.bind(this);
    this.findFreeSpot = this.findFreeSpot.bind(this);
    this.initDashboard = this.initDashboard.bind(this);
    this.getWidgetsInArea = this.getWidgetsInArea.bind(this);

    this.dashboardRef = React.createRef();
    this.maxColumns = 4;
    this.rowHeight = 50;
  }

  componentDidMount() {
      window.addEventListener("resize", this.resizeUpdate);

      this.initDashboard(false);
  }

  componentWillUnmount() {
    window.removeEventListener('resize', this.resizeUpdate)
  }

  resizeUpdate(){
    this.initDashboard();
    this.forceUpdate();
  }

  findFreeSpot(width, height){
    for(var y = 0; y < 20; y++){
        for(var x = 0; x <= this.maxColumns - width; x++){
            var result = this.getWidgetsInArea(x, y, width, height);
            if (result.length === 0)
                return {x: x, y: y};
        }
     }

     return null;
  }

  isFree(x, y)
  {
    for(var i = 0; i < this.widgetRefs.length; i++){
        var widget = this.widgetRefs[i];
        if(widget.x !== -1){
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
            var checkY = y + j;

            for(var k = 0; k < this.widgetRefs.length; k++){
                var widget = this.widgetRefs[k];
                if(result.indexOf(widget) !== -1)
                    continue;

                if(widget.x !== -1){
                    if (checkX >= widget.x && checkX < widget.x + widget.width
                    && checkY >= widget.y && checkY < widget.y + widget.height)
                        result.push(widget);
                }
            }
        }
    }
    return result;
  }

  initDashboard(){

    if(this.dashboardRef.current)
    {
        const dashboardWidth = this.dashboardRef.current.clientWidth;
        const columnWidth = dashboardWidth / this.maxColumns;

        for(var i = 0; i < this.widgetRefs.length; i++){
            var widget = this.widgetRefs[i];
            var minSize = widget.ref.current.getSize();
            var columns =  Math.min(Math.ceil((minSize.width + 20) / columnWidth), this.maxColumns);
            const rows = Math.ceil((minSize.height + 20) / this.rowHeight);

            if(columns === this.maxColumns - 1)
                columns = this.maxColumns;

            widget.x = -1;
            widget.y = -1;
            widget.width = columns;
            widget.height = rows;
            widget.style = {
                width: 0,
                height: 0,
                left: 0,
                top: 0
            };
        }

        for(var j = 0; j < this.widgetRefs.length; j++){
            var widgetj = this.widgetRefs[j];
            var pos = this.findFreeSpot(widgetj.width, widgetj.height);
            widgetj.x = pos.x;
            widgetj.y = pos.y;
        }

        for(var k = 0; k < this.widgetRefs.length; k++){
            var widgetk = this.widgetRefs[k];
            widgetk.style.left = (widgetk.x * columnWidth) + "px";
            widgetk.style.width = (widgetk.width * columnWidth) + "px";
            widgetk.style.top = (widgetk.y * this.rowHeight) + "px";
            widgetk.style.height = (widgetk.height * this.rowHeight) + "px";
        }
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