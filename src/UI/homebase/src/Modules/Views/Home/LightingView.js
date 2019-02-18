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
    this.updateGroup = this.updateGroup.bind(this);
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

  writeWarmthPercentage(value)
  {
    return Math.round((value - 250) / 204 * 100) + "%";
  }

  dimmerChange(group, value)
  {
    value = Math.round(value);
    console.log("Change " + group.name + " to " + value);
    this.updateGroup(group.id, "dimmer", value);
    axios.post(window.vars.apiBase + 'lighting/set_group_dimmer?group='+group.id+'&dimmer=' + value);
  }

  toggleGroup(group, value)
  {
    console.log("Change " + group.name + " to " + value);
    this.updateGroup(group.id, "state", value);
    axios.post(window.vars.apiBase + 'lighting/set_group_state?group='+group.id+'&state=' + value);
  }

  lightDimmerChange(group, light, value)
  {
    value = Math.round(value);
    console.log("Change " + light.name + " dimmer to " + value);
    this.updateLight(group.id, light.id, "dimmer", value);
    axios.post(window.vars.apiBase + 'lighting/set_light_dimmer?light='+light.id+'&dimmer=' + value);
  }

  lightWarmthChange(group, light, value)
  {
    value = Math.round(value);
    console.log("Change " + light.name + " warmth to " + value);
    this.updateLight(group.id, light.id, "color_temp", value);
    axios.post(window.vars.apiBase + 'lighting/set_light_warmth?light='+light.id+'&warmth=' + value);
  }

  toggleLight(group, light, value)
  {
    console.log("Change " + light.name + " to " + value);
    this.updateLight(group.id, light.id, "state", value);
    axios.post(window.vars.apiBase + 'lighting/set_light_state?light='+light.id+'&state=' + value);
  }

  groupTitleChange(group, newTitle)
  {
    this.updateGroup(group.id, "name", newTitle);
  }

  groupTitleSave(group, newTitle)
  {
      axios.post(window.vars.apiBase + 'lighting/set_group_name?group='+group.id+'&name=' + encodeURIComponent(newTitle));
  }

  lightTitleChange(group, light, newTitle)
  {
    this.setState(state =>
    ({
        lightData: state.lightData.map(s => {
            if(s.id === group.id){
                for(var i = 0; i < s.lights.length; i++)
                {
                    if(s.lights[i].id === light.id){
                        s.lights[i].name = newTitle;
                    }
                }
            }
            return s;
        })
    }));
  }

  lightTitleSave(light, newTitle)
  {
      axios.post(window.vars.apiBase + 'lighting/set_light_name?light='+light.id+'&name=' + encodeURIComponent(newTitle));
  }

  toggleGroupDetails(group)
  {
    this.updateGroup(group.id, "showDetails", !group.showDetails);

    if (!group.lights)
    {
        console.log("request light data for group " + group.name);
        axios.get(window.vars.apiBase + 'lighting/get_group_lights?group='+group.id).then(
            (data) => { console.log(data.data); return this.updateGroup(group.id, "lights", data.data); },
            (err) => { console.log (err) }
        )
    }
  }

  updateGroup(groupId, property, value)
  {
    this.setState(state =>
    ({
        lightData: state.lightData.map(s => {
            if(s.id === groupId)
                s[property] = value;
            return s;
        })
    }));
  }

  updateLight(groupId, lightId, property, value)
  {
    this.setState(state =>
    ({
        lightData: state.lightData.map(s => {
            if(s.id === groupId){
                for(var i = 0; i < s.lights.length; i++)
                {
                    if(s.lights[i].id === lightId){
                        s.lights[i].lights[0][property] = value;
                    }
                }
            }
            return s;
        })
    }));
  }

  render() {
    return (
      <div className="lighting-view">
        <ViewLoader loading={!this.state.lightData}/>
        { this.state.lightData &&
            this.state.lightData.map(lightGroup => {
                return(
                    <div key={lightGroup.id} className="light-group">
                        <InfoGroup title={lightGroup.name}
                                   titleChangeable={true}
                                   onTitleClick={() => this.toggleGroupDetails(lightGroup)}
                                   onTitleChange={(title) => this.groupTitleChange(lightGroup, title)}
                                   onSave={(title) => this.groupTitleSave(lightGroup, title)}>
                           <div className="light-group-content">
                                <div className="light-group-dimmer">
                                    <Slider format={this.writeDimmerPercentage} min={0} max={255} value={lightGroup.dimmer} onChange={(value) => this.dimmerChange(lightGroup, value)} />
                                </div>
                                <div className="light-group-state"><Switch value={lightGroup.state} onToggle={(value) => this.toggleGroup(lightGroup, value)} /></div>
                            </div>
                            { lightGroup.showDetails &&
                                <div className="light-group-details">

                                    { lightGroup.lights &&
                                        lightGroup.lights.map(light => {
                                            return (
                                                <InfoGroup key={light.id}
                                                           title={light.name}
                                                           titleChangeable={true}
                                                           onTitleChange={(title) => this.lightTitleChange(lightGroup, light, title)}
                                                           onSave={(title) => this.lightTitleSave(light, title)}>
                                                     <div className="light-group-light">
                                                         <div className="light-group-dimmer">
                                                            <Slider format={this.writeDimmerPercentage} formatMinMax={(value) => value == 0 ? "Dimmer": "" } min={0} max={255} value={light.lights[0].dimmer} onChange={(value) => this.lightDimmerChange(lightGroup, light, value)} />
                                                        </div>
                                                        <div className="light-group-state"><Switch value={light.lights[0].state} onToggle={(value) => this.toggleLight(lightGroup, light, value)} /></div>
                                                        { light.can_set_temp &&
                                                            <div className="light-group-warmth">
                                                                <Slider format={this.writeWarmthPercentage} formatMinMax={(value) => value == 250 ? "Warmth": "" } min={250} max={454} value={light.lights[0].color_temp} onChange={(value) => this.lightWarmthChange(lightGroup, light, value)} />
                                                            </div>
                                                        }
                                                    </div>
                                                </InfoGroup>

                                            )
                                        })

                                    }
                                </div>
                            }
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