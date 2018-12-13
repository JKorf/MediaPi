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
    this.pending_messages = [];
    this.wsConnected = false;
  }

  static socketOpen(){
    console.log("Websocket opened");
    this.wsConnected = true;

    this.ws.send(JSON.stringify({event: "init", type: "UI"}));
    this.subscriptions.forEach(sub => {
        if(!sub.subscribed)
            this.send_subscription(sub);
    });
  }

  static socketMessage(e){
    var data = JSON.parse(e.data);
    console.log("Received: ", data);

    if (data.type == "update"){
        var subscription = this.subscriptions.find(el => el.subscription_id == data.subscription_id);
        if(subscription)
            subscription.trigger(data.data);
    }
    else if(data.type === "response")
    {
        var id = data.request_id;
        var pending_message = this.pending_messages.find(el => el.request_id == id)
        if(pending_message)
            pending_message.resolve(true)
        else{
            this.subscriptions.forEach(sub =>
            {
                if(sub.request_id === id){
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

  static request(topic, params)
  {
    if (!this.wsConnected)
    {
        return new Promise((resolve, reject) =>{
            reject()
         });
    }

     var msg = {request_id: newId(), event: "request", topic: topic, params: params};
     var promise = new Promise((resolve, reject) =>{
        msg.resolve = resolve;
        msg.reject = reject;
     });
     this.pending_messages.push(msg);
     console.log("Requested: ", msg);
     this.ws.send(JSON.stringify(this.ignore(msg, ["resolve", "reject"])));
     return promise;
  }

  static subscribe(topic, callback) {
    var subbed;
    var id;

    this.subscriptions.forEach(el => {
        if(el.topic == topic){
            id = el.addCallback(callback);
            subbed = true;
        }
    });

    if(!subbed)
    {
        var newSub = new SocketSubscription(topic);
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
      var msg = {request_id: subscription.request_id, event: "subscribe", topic: subscription.topic};
      console.log("Requested: ", msg);
      this.ws.send(JSON.stringify(msg));
  }

  static send_unsubscription(subscription){
      this.subscriptions.remove(subscription);
      var msg = {request_id: subscription.subscription_id, event: "unsubscribe", topic: subscription.topic};
      console.log("Requested: ", msg);
      this.ws.send(JSON.stringify(msg));
  }

  static ignore(obj, keys)
    {
        var dup = {};
        for (var key in obj) {
            if (keys.indexOf(key) == -1) {
                dup[key] = obj[key];
            }
        }
        return dup;
    }
}

class SocketSubscription
{
    constructor(topic){
        this.request_id = 0
        this.subscription_id = 0

        this.topic = topic;
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

    trigger(data){
        this.callbacks.forEach(cb => cb.callback(data));
    }
}