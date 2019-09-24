import React, { Component } from 'react';
import axios from 'axios';

import Widget from './Widget.js';

class MoodsWidget extends Component {
  constructor(props) {
    super(props);

    this.state = {groups: []};
    this.getSize = this.getSize.bind(this);
  }

  shouldShow(){
    return true;
  }

  getSize(){
    return {width: 120, height: 135};
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
      <Widget {...this.props} >
        <div className="moods-widget-content">
            { this.state.moods && this.state.moods.map(mood => {
                    return(
                        <div className="moods-widget-mood" key={mood.id} onClick={e => this.selectMood(mood)} >
                            {mood.name}
                        </div>
                    );
                })
            }
        </div>
      </Widget>
    );
  }
};

export default MoodsWidget;