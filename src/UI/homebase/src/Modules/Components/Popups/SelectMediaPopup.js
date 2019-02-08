import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";
import Popup from "./Popup.js"
import Button from "./../Button"
import seenImage from './../../../Images/watched.svg';
import SvgImage from './../../Components/SvgImage';

import Socket from "./../../../Socket.js"

class SelectMediaPopup extends Component {
  constructor(props) {
    super(props);
    this.state = {};
    this.cancel = this.cancel.bind(this);
    this.select = this.select.bind(this);
    this.selectionChange = this.selectionChange.bind(this);
    console.log(this.props.files);
  }

  cancel()
  {
    this.props.onCancel();
    console.log("Cancel");
  }

  select()
  {
    var file = this.props.files.filter(f => f.path == this.state.selectedFile)[0];
    this.props.onSelect(file);
  }

  selectionChange (file) {
    console.log(file);
      this.setState({
        selectedFile: file
      });
    }


  render() {
    const buttons = (
        <div>
         <Button classId="secondary" text="Cancel" onClick={this.cancel} />
         <Button classId="secondary" text="Select"  onClick={this.select} />
         </div>
    )
    return (
    <Popup title="Select a file" loading={false} buttons={buttons} classId="select-media-popup">
        {this.props.files.map((file, index) => <div key={index}>
            <div className="media-file-select">
                <label className={"media-file-select-file " + (this.state.selectedFile === file.path ? "" : "truncate")}>
                    <input type="radio"
                          value={file.path}
                          checked={this.state.selectedFile === file.path}
                          onChange={(e) => this.selectionChange(e.target.value)} />
                          {file.path}
                        { file.seen && <div className="media-file-seen"><SvgImage src={seenImage} /></div> }
                </label>
             </div>
        </div>)}
    </Popup>
    )
  }
};
export default SelectMediaPopup;
