import React, { Component } from 'react';
import axios from 'axios';

import View from './../View.js';
import HDRow from './../../Components/HDRow';
import SelectInstancePopup from './../../Components/Popups/SelectInstancePopup.js';
import Popup from './../../Components/Popups/Popup.js';

import picImage from "./../../../Images/image.svg";
import streamImage from "./../../../Images/stream.svg";
import otherImage from "./../../../Images/other.svg";
import subImage from "./../../../Images/subtitle.svg";
import DirectoryImage from "./../../../Images/directory.svg";

class HDView extends Component {
  constructor(props) {
    super(props);
    this.state = {structure: {files: [], dirs: []}, showPopup: false, loading: true};

    this.path = "C:/";

    this.selectedFile = null;
    this.props.changeBack({ to: "/mediaplayer/" });

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
    this.props.changeBack({ action: () => this.dirUp() });
  }

  dirUp(){
    var lastIndex = this.path.lastIndexOf("/");

    if(this.isBaseFolder(this.path))
        return;

    if(lastIndex == this.path.length - 1)
        this.path = this.path.substring(0, this.path.length - 1);

    this.path = this.path.substring(0, this.path.lastIndexOf("/")+1);
    this.loadFolder(this.path);

    if(this.isBaseFolder(this.path))
        this.props.changeBack({ to: "/mediaplayer/" });
  }

  isBaseFolder(dir){
    return (dir.match(/\//g) || []).length == 1;
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
    this.setState({showPopup: false, loading: true});
    axios.post('http://localhost/play/file?instance=' + instance + "&path=" + encodeURIComponent(this.selectedFile) + "&position=0")
    .then(
        () => this.setState({loading: false}),
        ()=> this.setState({loading: false})
    );
  }

  loadFolder(){
      this.setState({loading: true});
      axios.get('http://localhost/hd/directory?path=' + this.path).then(data => {
            console.log(data.data);
            this.setState({structure: data.data, loading: false});
        }, err =>{
            console.log(err);
            this.setState({loading: false});
        });
    }

  getFileIcon(file)
  {
    if (file.endsWith(".mkv") || file.endsWith("mp4") || file.endsWith("avi") || file.endsWith("wmv"))
        return streamImage;

    if (file.endsWith("png") || file.endsWith("jpg"))
        return picImage;

    if (file.endsWith(".srt"))
        return subImage;

    return otherImage;
  }

  render() {
    const structure = this.state.structure;
    const showPopup = this.state.showPopup;
    const loading = this.state.loading;

    return (
      <div className="hd">
        { structure.dirs.map((dir, index) => <HDRow key={index} img={DirectoryImage} text={dir} clickHandler={(e) => this.dirClick(dir, e)}></HDRow>) }
        { structure.files.map((file, index) => <HDRow key={index} img={this.getFileIcon(file)} text={file} clickHandler={(e) => this.fileClick(file, e)}>{file}</HDRow>) }
        { showPopup &&
            <SelectInstancePopup onCancel={this.instanceSelectCancel} onSelect={this.instanceSelect} />
        }
        { loading &&
            <Popup loading={loading} />
        }
      </div>
    );
  }
};

export default HDView;