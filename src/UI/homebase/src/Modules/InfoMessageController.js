import React, { Component } from 'react';

import InfoMessage from './../Modules/Components/InfoMessage/'

class InfoMessageController extends Component {
  constructor(props) {
    super(props);

    this.state = {msgs: []};
    this.msgId = 0;
    this.addMessage = this.addMessage.bind(this);
    this.removeMessage = this.removeMessage.bind(this);
  }

  componentDidMount() {
  }

  componentWillUnmount(){
  }

  addMessage(time, type, header, text, linkText, linkTo)
  {
    var newMsgs = this.state.msgs;
    newMsgs.push({id: this.msgId++, time: time, type: type, header: header, text: text, linkText: linkText, linkTo: linkTo});
    this.setState({msgs: newMsgs});
  }

  removeMessage(msg)
  {
    var newMsgs = this.state.msgs;
    newMsgs.splice(newMsgs.indexOf(msg), 1);
    this.setState({msgs: newMsgs});
  }

  render()
  {
    return (
        <div className="info-message-holder">
        {
            this.state.msgs.map((msg, index) =>
            {
                return <InfoMessage key={msg.id} type={msg.type} header={msg.header} time={msg.time} text={msg.text} linkText={msg.linkText} linkTo={msg.linkTo} onDone={() => this.removeMessage(msg)} />
            })
        }
        </div>
    )
  }
};

export default InfoMessageController;