import React, { Component } from 'react';
import axios from 'axios';

import { InfoGroup } from './../../Components/InfoGroup';
import ViewLoader from './../../Components/ViewLoader';
import Slider from './../../Components/Slider';
import Switch from './../../Components/Switch';

class LightingView extends Component {
  constructor(props) {
    super(props);
    this.state = {};

    this.props.functions.changeBack({ to: "/home/" });
    this.props.functions.changeTitle("Lights");
    this.props.functions.changeRightImage(null);

  }

  componentDidMount() {
    axios.get(window.vars.apiBase + 'lighting/get_groups').then(
        (data) => {
            this.setState({lightData: data.data});
            console.log(data.data);
         },
        (error) => { console.log(error) }
    )
  }

  writeDimmerPercentage(value)
  {
    return Math.round(value / 255 * 100) + "%";
  }

  dimmerChange(group, value)
  {
    value = Math.round(value);
    console.log("Change " + group.name + " to " + value);

    this.setState(state => {
      const lightData = state.lightData.map(s => {
        if(s.id === group.id){
            s.dimmer = value;
        }
        return s;
      });

      return {
        lightData,
      };
    });

    axios.post(window.vars.apiBase + 'lighting/set_group_dimmer?group='+group.id+'&dimmer=' + value);
  }

  toggleGroup(group, value)
  {
    console.log("Change " + group.name + " to " + value);
    this.setState(state => {
      const lightData = state.lightData.map(s => {
        if(s.id === group.id){
            s.state = value;
        }
        return s;
      });

      return {
        lightData,
      };
    });
    axios.post(window.vars.apiBase + 'lighting/set_group_state?group='+group.id+'&state=' + value);
  }

  titleChange(group, newTitle)
  {
    this.setState(state => {
      const lightData = state.lightData.map(s => {
        if(s.id === group.id){
            s.name = newTitle;
        }
        return s;
      });

      return {
        lightData,
      };
    });
  }

  titleSave(group, newTitle)
  {
      axios.post(window.vars.apiBase + 'lighting/set_group_name?group='+group.id+'&name=' + encodeURIComponent(newTitle));
  }

  render() {
    return (
      <div className="lighting-view">
        <ViewLoader loading={!this.state.lightData}/>
        { this.state.lightData &&
            this.state.lightData.map(lightGroup => {
                return(
                    <div key={lightGroup.id} className="light-group">
                        <InfoGroup title={lightGroup.name} titleChangeable={true} onTitleChange={(title) => this.titleChange(lightGroup, title)} onTitleSave={(title) => this.titleSave(lightGroup, title)}>
                            <div className="light-group-dimmer">
                                <Slider format={this.writeDimmerPercentage} min={0} max={255} value={lightGroup.dimmer} onChange={(value) => this.dimmerChange(lightGroup, value)} />
                            </div>
                            <div className="light-group-state"><Switch value={lightGroup.state} onToggle={(value) => this.toggleGroup(lightGroup, value)} /></div>
                            <div className="light-group-details"></div>
                        </InfoGroup>
                    </div>
                );
            })
        }
      </div>
    );
  }
};

export default LightingView;