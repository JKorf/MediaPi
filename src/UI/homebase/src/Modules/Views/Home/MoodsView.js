import React, { Component } from 'react';
import axios from 'axios';

import AddMoodPopup from './../../Components/Popups/AddMoodPopup.js';
import { InfoGroup } from './../../Components/InfoGroup'
import addImg from './../../../Images/plus.svg'

class MoodsView extends Component {
  constructor(props) {
    super(props);
    this.state = {showAdd: false};
    this.props.functions.changeBack({ to: "/home/" });
    this.props.functions.changeTitle("Moods");
    this.props.functions.changeRightImage(null);

    this.showAdd = this.showAdd.bind(this);
  }

  componentDidMount() {
      axios.get(window.vars.apiBase + 'home/moods').then(data => {
                console.log(data.data);
                this.setState({moods: data.data});
            }, err =>{
                console.log(err);
            });
  }

  addMood(name){
    axios.post(window.vars.apiBase + "home/add_mood?name=" + encodeURIComponent(name)).then(response => {
        var current = this.state.moods;
        current.push({id: response.data + "", name: name});
        this.setState({moods: current});
    });
    this.setState({showAdd: false});
  }

  showAdd(){
    this.setState({showAdd: true});
  }

  removeMood(mood){
    if(window.confirm("Do you want to remove mood " + mood.name + "?")){
        axios.post(window.vars.apiBase + "home/remove_mood?id=" + mood.id);
        this.setState({moods: this.state.moods.filter(x => x.id !== mood.id)});
    }
  }

  render() {

    return (
      <div className="moods-view">
        { this.state.showAdd && <AddMoodPopup onAdd={e => this.addMood(e)} onCancel={e => this.setState({showAdd: false})} /> }

         { this.state.moods &&
            <div className="moods">
                <InfoGroup title="Moods" configurable={true} configureIcon={addImg} onConfigure={this.showAdd}>
                { this.state.moods.map(mood =>
                    <div className="mood" key={mood.id}>
                        <div className="mood-name">{mood.name}</div>
                        <div className="mood-actions">
                            <div className="mood-remove" onClick={e => this.removeMood(mood)}>remove</div>
                        </div>
                    </div>
                )}
                {this.state.moods.length == 0 &&
                    <div className="no-moods">No moods defined yet</div>
                }
                </InfoGroup>
            </div>
         }
      </div>
    );
  }
};

export default MoodsView;