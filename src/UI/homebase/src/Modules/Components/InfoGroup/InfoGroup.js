import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";
import SvgImage from "./../SvgImage"

import settingsImage from './../../../Images/edit.svg'
import saveImage from './../../../Images/save.svg'

class InfoGroup extends Component {
  constructor(props) {
    super(props);

    this.state = {editingTitle: false};
  }

  editTitle()
  {
    if(this.props.onEditStart)
        this.props.onEditStart();
    this.setState({editingTitle: true});
  }

  changeTitle(e){
    this.props.onTitleChange(e.target.value);
  }

  saveTitle()
  {
    this.props.onSave(this.props.title);
    this.setState({editingTitle: false});
  }

  onTitleClick(){
    if(this.props.onTitleClick)
        this.props.onTitleClick();
  }

  render() {
    return (
      <div className="player-details-group">
        <div className="player-details-group-title">
            { !this.state.editingTitle && <div className="info-group-title-value" onClick={() => this.onTitleClick()}>{this.props.title}</div> }
            { this.state.editingTitle && <div className="info-group-title-edit"><input onChange={(e) => this.changeTitle(e)} type="text" value={this.props.title} /></div> }
            { this.props.titleChangeable && !this.state.editingTitle && <div className="info-group-title-change" onClick={() => this.editTitle()}><SvgImage src={settingsImage} /></div>}
            { this.props.titleChangeable && this.state.editingTitle && <div className="info-group-title-change" onClick={() => this.saveTitle()}><SvgImage src={saveImage} /></div>}
        </div>
        <div className="player-details-group-content">{this.props.children}</div>
    </div>
    );
  }
}

export default InfoGroup;