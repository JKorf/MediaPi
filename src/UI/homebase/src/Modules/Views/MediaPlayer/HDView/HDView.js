import React, { Component } from 'react';
import axios from 'axios';

import View from './../../View';
import HDRow from './../../../Components/HDRow';
import SelectInstancePopup from './../../../Components/Popups/SelectInstancePopup.js';

import FileImage from "./../../../../Images/image.svg";
import DirectoryImage from "./../../../../Images/directory.svg";

class HDView extends Component {
  constructor(props) {
    super(props);
    this.state = {structure: {files: [], dirs: []}, showPopup: false};

    this.path = "C:/";
    if(this.props.match.params.path)
        this.path = this.props.match.params.path;

    this.selectedFile = null;
    this.props.changeBack({ action: () => this.dirUp() });

    this.instanceSelectCancel = this.instanceSelectCancel.bind(this);
    this.instanceSelect = this.instanceSelect.bind(this);
    this.dirUp = this.dirUp.bind(this);
  }

  componentDidMount() {
    this.loadFolder();
  }

  dirClick(dir){
    if (!this.path.endsWith("/"))
        this.path += "/";

    this.path += dir + "/";
    this.loadFolder(this.path);
  }

  dirUp(){
    var lastIndex = this.path.lastIndexOf("/");

    if((this.path.match(/\//g) || []).length == 1){
        return;
    }

    if(lastIndex == this.path.length - 1)
        this.path = this.path.substring(0, this.path.length - 1);

    this.path = this.path.substring(0, this.path.lastIndexOf("/")+1);
    this.loadFolder(this.path);
  }

  fileClick(file)
  {
    this.selectedFile = this.path + file;
    this.setState({showPopup: true});
  }

  instanceSelectCancel()
  {
    this.setState({showPopup: false});
  }

  instanceSelect(instance)
  {
    this.setState({showPopup: false});
    axios.post('http://localhost/hd/play_file?instance=' + instance + "&path=" + this.selectedFile + "&position=0");

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
        <SelectInstancePopup show={showPopup} onCancel={this.instanceSelectCancel} onSelect={this.instanceSelect} />
      </div>
    );
  }
};

export default HDView;