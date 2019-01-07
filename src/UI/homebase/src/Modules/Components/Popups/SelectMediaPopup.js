import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from "react-router-dom";
import Popup from "./Popup.js"
import Button from "./../Button"

import Socket from "./../../../Socket.js"

class SelectMediaPopup extends Component {
  constructor(props) {
    super(props);
    this.state = {};
    this.cancel = this.cancel.bind(this);
    this.select = this.select.bind(this);
    this.selectionChange = this.selectionChange.bind(this);
  }

  cancel()
  {
    this.props.onCancel();
    console.log("Cancel");
  }

  select()
  {
    this.props.onSelect(this.state.selectedFile);
  }

  selectionChange (file) {
      this.setState({
        selectedFile: file
      });
    }


  render() {
    console.log(this.props.files);
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
            <input type="radio" value={file.path}
                      checked={this.state.selectedFile === file.path}
                      onChange={(e) => this.selectionChange(e.target.value)} />
              <div onClick={(e) => this.selectionChange(file.path)} className={"media-file-select-file " + (this.state.selectedFile == file.path ? "" : "truncate")}>{file.path}</div>
             </div>
        </div>)}
    </Popup>
    )
  }
};
export default SelectMediaPopup;
