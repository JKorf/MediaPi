import React, { Component } from 'react';
import axios from 'axios'

import View from './../../View'
import HDRow from './../../../Components/HDRow'

import FileImage from "./../../../../Images/image.svg"
import DirectoryImage from "./../../../../Images/directory.svg"

class HDView extends Component {
  constructor(props) {
    super(props);
    this.path = "C:/";
    this.state = {structure: {files: [], dirs: []}};
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
    return (
      <div className="hd">
        { structure.dirs.map((dir, index) => <HDRow key={index} img={DirectoryImage} text={dir} onClick={(e) => this.dirClick(dir, e)}></HDRow>) }
        { structure.files.map((file, index) => <HDRow key={index} img={FileImage} text={file} className="hd-file">{file}</HDRow>) }
      </div>
    );
  }
};

export default HDView;