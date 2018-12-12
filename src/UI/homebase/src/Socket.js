import newId from './Utils/id.js'

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
        var subscription = this.subscriptions.find(el => el.subscription_id == data.id);
        if(subscription)
            subscription.trigger(data.data);
    }
    else if(data.type === "response")
    {
        if(data.event === "subscribed")
        {
            this.subscriptions.forEach(sub =>
            {
                if(sub.request_id === data.id){
                    sub.subscription_id = data.data[0];
                }
            });
        }
    }
  }

  static socketClose(){
     console.log("Websocket closed");
     this.wsConnected = false;
     this.subscriptions.forEach(sub => { sub.subscribed = false; });
  }

  static subscribe(topic, params, callback) {
    var subbed;
    var id;

    if (!Array.isArray(params))
        params = [params];

    this.subscriptions.forEach(el => {
        if(el.matches(topic, params)){
            id = el.addCallback(callback);
            subbed = true;
        }
    });

    if(!subbed)
    {
        var newSub = new SocketSubscription(topic, params);
        this.subscriptions.push(newSub);
        id = newSub.addCallback(callback);
        if(this.wsConnected)
            this.send_subscription(newSub);
    }

    return id;
  }

  static unsubscribe(subId)
  {
     this.subscriptions.forEach(sub =>{
        if(sub.removeCallback(subId))
        {
            if(sub.callbacks.length == 0){
                this.send_unsubscription(sub);
                return;
            }
        }
     });
  }

  static send_subscription(subscription){
      subscription.subscribed = true;
      subscription.request_id = newId()
      this.ws.send(JSON.stringify({id: subscription.request_id, event: "subscribe", topic: subscription.topic, params: subscription.params}));
  }

  static send_unsubscription(subscription){
      this.subscriptions.remove(subscription);
      this.ws.send(JSON.stringify({id: subscription.subscription_id, event: "unsubscribe", topic: subscription.topic}));
  }
}

class SocketSubscription
{
    constructor(topic, params){
        this.request_id = 0
        this.subscription_id = 0

        this.topic = topic;
        this.params = params;
        this.callbacks = [];
        this.subscribed = false;
    }

    addCallback(callback){
        const id = newId();
        this.callbacks.push({id: id, callback: callback});
        return id;
    }

    removeCallback(id){
        for (var i = 0; i < this.callbacks.length; i++)
        {
            if(this.callbacks[i].id == id)
            {
                this.callbacks.remove(this.callbacks[i]);
                return true;
            }
        }
        return false;
    }

    matches(topic, params){
        if(this.topic !== topic)
            return false;

        if(this.params.length != params.length)
            return false;

        for(var i = 0 ; i < this.params.length; i++)
        {
            if(this.params[i] !== params[i])
                return false;
        }

        return true;
    }

    trigger(data){
        this.callbacks.forEach(cb => cb.callback(data));
    }
}