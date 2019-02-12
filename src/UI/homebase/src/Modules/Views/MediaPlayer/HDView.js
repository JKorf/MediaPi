import React, { Component } from 'react';
import axios from 'axios';

import MediaPlayerView from './../MediaPlayer/MediaPlayerView.js';
import HDRow from './../../Components/HDRow';

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
    this.props.functions.changeBack({ to: "/mediaplayer/" });
    this.props.functions.changeTitle("Hard drive");
    this.props.functions.changeRightImage(null);
    this.promise = null;

    this.dirUp = this.dirUp.bind(this);
    this.dirClick = this.dirClick.bind(this);
    this.playMedia = this.playMedia.bind(this);
    this.filterFiles = this.filterFiles.bind(this);
  }

  componentDidMount() {
    this.loadFolder();
  }

  dirClick(dir){
    if (!this.path.endsWith("/"))
        this.path += "/";

    this.path += dir + "/";
    this.loadFolder(this.path);
    this.props.functions.changeBack({ action: () => this.dirUp() });
  }

  dirUp(){
    var lastIndex = this.path.lastIndexOf("/");

    if(this.isBaseFolder(this.path))
        return;

    if(lastIndex === this.path.length - 1)
        this.path = this.path.substring(0, this.path.length - 1);

    this.path = this.path.substring(0, this.path.lastIndexOf("/")+1);
    this.loadFolder(this.path);

    if(this.isBaseFolder(this.path))
        this.props.functions.changeBack({ to: "/mediaplayer/" });
  }

  isBaseFolder(dir){
    return (dir.match(/\//g) || []).length === 1;
  }

  fileClick(file)
  {
    this.viewRef.current.play({url: this.path + file.name, title: file.name, position: file.continue_time, length: file.total_time});
  }

  playMedia(instance, file){
    var toSee = file.length - file.position;
    var shouldContinue = file.position > 1000 * 60 && toSee > 1000 * 60;
    console.log("Continue from " + file.position);

    axios.post('http://'+window.location.hostname+'/play/file?instance=' + instance + "&path=" + encodeURIComponent(file.url) + "&position=" + (shouldContinue ? file.position + "": "0"))
    .then(
        () =>
        {
            if(this.viewRef.current) this.viewRef.current.changeState(1);
        },
        () => { if(this.viewRef.current) this.viewRef.current.changeState(1); }
    );
  }

  loadFolder(){
      this.viewRef.current.changeState(0);
      axios.get('http://'+window.location.hostname+'/hd/directory?path=' + this.path).then(data => {
            if(this.viewRef.current) { this.viewRef.current.changeState(1); }
            console.log(data.data);
            this.setState({structure: data.data});
            this.filterFiles();
        }, err =>{
            if(this.viewRef.current) { this.viewRef.current.changeState(1); }
            console.log(err);
        });
    }

  filterFiles(){
    var extensions = [".mkv", ".avi", ".mp4", ".mpg", "wmv"]
    var structure = this.state.structure;
    structure.files = structure.files.filter(f => {
        for(var i = 0; i < extensions.length; i++)
            if(f.name.endsWith(extensions[i]))
                return true;
        return false;
    });
    this.setState({structure: structure});
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
        { structure.dirs.map((dir, index) => <HDRow key={dir} img={DirectoryImage} text={dir} clickHandler={(e) => this.dirClick(dir, e)}></HDRow>) }
        { structure.files.map((file, index) => <HDRow key={file.name} img={this.getFileIcon(file.name)} text={file.name} seen={file.seen} clickHandler={(e) => this.fileClick(file, e)}></HDRow>) }
      </MediaPlayerView>
    );
  }
};

export default HDView;