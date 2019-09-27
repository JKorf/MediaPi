import React, { Component } from 'react';
import axios from 'axios';

import Widget from './Widget.js';

class MoodsWidget extends Component {
  constructor(props) {
    super(props);

    this.state = {moods: []};
    this.getSize = this.getSize.bind(this);
  }

  shouldShow(){
    return this.state.moods.length > 0;
  }

  getSize(){
    return {width: 140, height: 135};
  }

  componentDidMount() {
     axios.get(window.vars.apiBase + 'home/moods').then(data => {
                console.log(data.data);
                this.setState({moods: data.data});
            }, err =>{
                console.log(err);
            });
  }

  componentWillUnmount(){
  }

  selectMood(mood){
    axios.post(window.vars.apiBase + 'home/select_mood?id='+mood.id);
  }

  render() {
    return (

        <div className="moods-widget-wrapper">
            <div className="moods-widget-content">
                { this.state.moods.map(mood => {
                        return(
                            <div className="moods-widget-mood" key={mood.id} onClick={e => this.selectMood(mood)} >
                                <div className="moods-widget-mood-wrapper">
                                    <div className="moods-subtitle">mood</div>
                                    <div className="moods-name">{mood.name}</div>
                                </div>
                            </div>
                        );
                    })
                }
            </div>
        </div>
    );
  }
};

export default MoodsWidget;