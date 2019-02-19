import React, { Component } from 'react';
import Popup from "./Popup.js"
import Button from "./../Button"
import seenImage from './../../../Images/watched.svg';
import SvgImage from './../../Components/SvgImage';

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

  select(start_from)
  {
    var file = this.props.files.filter(f => f.path === this.state.selectedFile)[0];
    this.props.onSelect(file, start_from);
  }

  selectionChange (file) {
    console.log(file);
      this.setState({
        selectedFile: file
      });
    }

    writeTimespan(duration)
      {
         duration = Math.round(duration);
         var seconds = parseInt((duration / 1000) % 60),
          minutes = parseInt((duration / (1000 * 60)) % 60),
          hours = parseInt((duration / (1000 * 60 * 60)) % 24);

          hours = (hours < 10) ? "0" + hours : hours;
          minutes = (minutes < 10) ? "0" + minutes : minutes;
          seconds = (seconds < 10) ? "0" + seconds : seconds;

          if (hours > 0)
            return hours + ":" + minutes + ":" + seconds;
          return minutes + ":" + seconds;
      }

  render() {
    const buttons = (
        <div>
         <Button classId="secondary" text="Cancel" onClick={this.cancel} />
         </div>
    )
    return (
    <Popup title="Select a file" loading={false} buttons={buttons} classId="select-media-popup">
        {this.props.files.map((file, index) =>
            <div className={"media-file-select " + (this.state.selectedFile === file.path ? "selected" : "")} key={file.path}>
                <div className={"media-file-select-file " + (this.state.selectedFile === file.path ? "" : "truncate")}>
                    <div className="media-file-select-title" onClick={(e) => this.selectionChange(file.path)}>{file.path}</div>
                    { this.state.selectedFile === file.path &&
                        <div className="media-file-select-details">
                            <Button text="Select" onClick={(e) => this.select(0)} classId="secondary"/>
                            { file.played_for > 1000 * 60 && <Button text={"Continue from " + this.writeTimespan(file.played_for)} onClick={() => this.select(file.played_for)} classId="secondary"></Button> }
                        </div>
                    }

                    { file.seen && <div className="media-file-seen"><SvgImage src={seenImage} /></div> }
                </div>
        </div>)}
    </Popup>
    )
  }
};
export default SelectMediaPopup;
