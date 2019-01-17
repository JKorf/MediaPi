import React, { Component } from 'react';
import axios from 'axios';
import videoFile from './../../../Images/video_file.png';

class HistoryView extends Component {
  constructor(props) {
    super(props);
    this.props.functions.changeBack({to: "/mediaplayer/" });
    this.props.functions.changeTitle("History");
    this.props.functions.changeRightImage(null);

    this.states = ["loading", "nothing"];
    this.state = {history: []};
  }

  componentDidMount() {
    axios.get('http://'+window.location.hostname+'/play/history').then(
        (data) => {
            this.setState({history: data.data.sort((a, b) =>  b.watched_at - a.watched_at)});
            console.log(data);
         },
        (error) => { console.log(error) }
    )
  }

  componentWillUnmount(){
  }

  render() {
    return (
        <div className='history'>

            { this.state.history.map((history, index) => { return (
                <div className="history-item" key={history.id}>
                    <div className="history-item-image"><img src={(history.image ? history.image: videoFile)} /></div>
                    <div className="history-item-details">
                        <div className="history-item-title truncate2">{history.title}</div>
                        <div className="history-item-type">{history.type}</div>
                        <div className="history-item-time">{new Intl.DateTimeFormat('en-GB', { year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(1970, 0, 0).setTime(history.watched_at))}</div>
                    </div>
                </div>)
            }) }

        </div>
    );
  }
};

export default HistoryView;