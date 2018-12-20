import React, { Component } from 'react';
import axios from 'axios'

import View from './../../View'
import HDRow from './../../../Components/HDRow'
import SelectPopup from './../../../Components/Popups/SelectPopup'

import FileImage from "./../../../../Images/image.svg"
import DirectoryImage from "./../../../../Images/directory.svg"

class HDView extends Component {
  constructor(props) {
    super(props);
    this.path = "C:/";
    this.state = {structure: {files: [], dirs: []}, showPopup: false};
  }

  componentDidMount() {
    this.loadFolder();
  }

  dirClick(dir){
    if (!this.path.endsWith("/"))
        this.path += "/";
    this.path += dir;
    this.loadFolder(dir);
  }

  fileClick(file)
  {
    this.setState({showPopup: true});
    console.log(file);
    //axios.post('http://localhost/hd/play_file', {params: { instance: this.props.i } }?instance='+this.props.instance + "&path=C:/jellies.mp4&position=0");
  }

  loadFolder(){
      axios.get('http://localhost/hd/directory?path=' + this.path).then(data => {
            console.log(data.data);
            this.setState({structure: data.data});
        }, err =>{
            console.log(err);
        });
    }

  render() {
    const structure = this.state.structure;
    const showPopup = this.state.showPopup;
    return (
      <div className="hd">
        { structure.dirs.map((dir, index) => <HDRow key={index} img={DirectoryImage} text={dir} clickHandler={(e) => this.dirClick(dir, e)}></HDRow>) }
        { structure.files.map((file, index) => <HDRow key={index} img={FileImage} text={file} clickHandler={(e) => this.fileClick(file, e)}>{file}</HDRow>) }
        <SelectPopup title="Select a mediaplayer" show={showPopup}>Test</SelectPopup>
      </div>
    );
  }
};

export default HDView;