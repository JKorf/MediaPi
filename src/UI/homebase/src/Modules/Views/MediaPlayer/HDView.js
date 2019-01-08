import React, { Component } from 'react';
import axios from 'axios';

import View from './../View.js';
import MediaPlayerView from './../MediaPlayer/MediaPlayerView.js';
import HDRow from './../../Components/HDRow';
import SelectInstancePopup from './../../Components/Popups/SelectInstancePopup.js';
import Popup from './../../Components/Popups/Popup.js';
import StartMediaPopup from './../../Components/Popups/StartMediaPopup.js';

import picImage from "./../../../Images/image.svg";
import streamImage from "./../../../Images/stream.svg";
import otherImage from "./../../../Images/other.svg";
import subImage from "./../../../Images/subtitle.svg";
import DirectoryImage from "./../../../Images/directory.svg";

class HDView extends Component {
  constructor(props) {
    super(props);
    this.state = {structure: {files: [], dirs: []}, selectedFile: null};
    this.viewRef = React.createRef();

    this.path = "C:/";
    this.props.changeBack({ to: "/mediaplayer/" });
    this.props.changeTitle("Hard drive");

    this.dirUp = this.dirUp.bind(this);
    this.dirClick = this.dirClick.bind(this);
    this.playMedia = this.playMedia.bind(this);
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
    this.viewRef.current.play({url: this.path + file, title: file});
  }

  playMedia(instance, file){
    axios.post('http://localhost/play/file?instance=' + instance + "&path=" + encodeURIComponent(file.url) + "&position=0")
    .then(
        () => this.viewRef.current.changeState(1),
        () => this.viewRef.current.changeState(1)
    );
  }

  loadFolder(){
      this.viewRef.current.changeState(0);
      axios.get('http://localhost/hd/directory?path=' + this.path).then(data => {
            this.viewRef.current.changeState(1);
            console.log(data.data);
            this.setState({structure: data.data});
        }, err =>{
            this.viewRef.current.changeState(1);
            console.log(err);
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

    return (
      <MediaPlayerView ref={this.viewRef} playMedia={this.playMedia}>
        { structure.dirs.map((dir, index) => <HDRow key={index} img={DirectoryImage} text={dir} clickHandler={(e) => this.dirClick(dir, e)}></HDRow>) }
        { structure.files.map((file, index) => <HDRow key={index} img={this.getFileIcon(file)} text={file} clickHandler={(e) => this.fileClick(file, e)}>{file}</HDRow>) }
      </MediaPlayerView>
    );
  }
};

export default HDView;