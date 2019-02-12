import React, { Component } from 'react';
import axios from 'axios';

import { InfoGroup } from './../../Components/InfoGroup';

class LightingView extends Component {
  constructor(props) {
    super(props);
    this.state = {};

    this.props.functions.changeBack({ to: "/home/" });
    this.props.functions.changeTitle("Lights");
    this.props.functions.changeRightImage(null);

  }

  componentDidMount() {
    axios.get('http://'+window.location.hostname+'/lighting/get_lights').then(
        (data) => {
            this.setState({lightData: data.data});
            console.log(data.data);
         },
        (error) => { console.log(error) }
    )
  }

  render() {
    return (
      <div className="lighting-view">
        Lights!
      </div>
    );
  }
};

export default LightingView;