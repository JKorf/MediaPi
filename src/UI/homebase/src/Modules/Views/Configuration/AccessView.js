import React, { Component } from 'react';

class AccessView extends Component {
  constructor(props) {
    super(props);

    this.state = {};

    this.props.functions.changeBack({});
    this.props.functions.changeTitle("Access");
    this.props.functions.changeRightImage(null);
  }

  componentDidMount() {
  }

  componentWillUnmount() {
  }

  render() {
    return <div className="settings-view">
        Test
    </div>
  }
};

export default AccessView;