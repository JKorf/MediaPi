import React, { Component } from 'react';
import SvgImage from "./../SvgImage"

import editImage from './../../../Images/edit.svg'
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
      <div className="info-group-box">
        <div className="info-group-box-title">
            { this.props.icon && <div className="info-group-title-icon"><SvgImage src={this.props.icon} /></div>}

            { !this.state.editingTitle && <div className={"info-group-title-value " + (this.props.icon ? "with-icon": "")} onClick={() => this.onTitleClick()}>{this.props.title}</div> }
            { this.state.editingTitle && <div className={"info-group-title-edit "  + (this.props.icon ? "with-icon": "")}><input onChange={(e) => this.changeTitle(e)} type="text" value={this.props.title} /></div> }
            { this.props.titleChangeable && !this.state.editingTitle && <div className="info-group-title-change" onClick={() => this.editTitle()}><SvgImage src={editImage} /></div>}
            { this.props.titleChangeable && this.state.editingTitle && <div className="info-group-title-change" onClick={() => this.saveTitle()}><SvgImage src={saveImage} /></div>}

            { this.props.configurable && <div className="info-group-title-change" onClick={() => this.props.onConfigure()}><SvgImage src={this.props.configureIcon} /></div>}
        </div>
        <div className="info-group-box-content">{this.props.children}</div>
    </div>
    );
  }
}

export default InfoGroup;