export default class WS {
  static init() {
    this.ws = new WebSocket('ws://localhost/ws');

    this.socketOpen = this.socketOpen.bind(this);
    this.socketMessage = this.socketMessage.bind(this);
    this.socketClose = this.socketClose.bind(this);

    this.ws.onopen = this.socketOpen;
    this.ws.onmessage = this.socketMessage;
    this.ws.close = this.socketClose;

    this.subscriptions = [];
    this.wsConnected = false;
  }

  static socketOpen(){
    console.log("Websocket opened");
    this.wsConnected = true;
    this.subscriptions.forEach(sub => {
        if(!sub.subscribed)
            this.send_subscription(sub);
    });
  }

  static socketMessage(e){
    var data = JSON.parse(e.data);
    console.log(data);

    if (data.type == "notify"){
        this.subscriptions.forEach(sub =>
        {
            if(sub.topic === data.event)
                sub.trigger(data.data);
        });
    }
  }

  static socketClose(){
     console.log("Websocket closed");
     this.wsConnected = false;
     this.subscriptions.forEach(sub => { sub.subscribed = false; });
  }

  static subscribe(topic, callback) {
    var subbed;
    this.subscriptions.forEach(el =>{
        if(el.topic === topic){
            el.addCallback(callback);
            subbed = true;
        }
    });

    if(!subbed)
    {
        this.subscriptions.push(new SocketSubscription(topic, callback));
        if(this.wsConnected)
            this.send_subscription(topic);
    }
  }

  static send_subscription(subscription){
      subscription.subscribed = true;
      this.ws.send(JSON.stringify({event: "subscribe", topic: subscription.topic}));
  }
}

class SocketSubscription
{
    constructor(topic, callback){
        this.topic = topic;
        this.callbacks = [callback];
        this.subscribed = false;
    }

    addCallback(callback){
        this.callbacks.push(callback);
    }

    trigger(data){
        this.callbacks.forEach(cb => cb(data));
    }
}