import newId from './Utils/id.js'
import openSocket from 'socket.io-client';

export default class WS {

    static init(){
        this.socket = null;
        this.connecting = false;
        this.authenticated = false;
        this.subscriptions = [];
        this.request_handlers = [];
    }

    static connect(){
        this.socket = openSocket(window.vars.websocketBase, { transports: ['websocket'] });
        this.socket.on('connect', () => {
            console.log("Websocket connected");
            this.socket.emit('init', localStorage.getItem('Client-ID'), sessionStorage.getItem('Session-Key'), (data) => this.processAuthResult(data));
        });
        this.socket.on('disconnect', () => {
            console.log("Websocket disconnected"); // will automatically reconnect when disconnected
        });

        this.socket.on('update', (topic, data) => {
            //console.log("Received update: " + topic + ", data: " + data);
            data = JSON.parse(data);
            for(var i = 0; i < this.subscriptions.length; i++){
                if(this.subscriptions[i].topic === topic){
                    this.subscriptions[i].trigger(data);
                }
            }
        });

        this.socket.on('request', (id, topic, data) => {
            console.log("Received request: " + topic + ", data: " + data);
            data = JSON.parse(data);
            var handler = this.request_handlers.find(el => el.name === topic);
            if (!handler){
                console.log("No handler for " + topic + " found");
                return
            }

            handler.handler(id, ...data);
        });
    }

    static processAuthResult(data){
        console.log("Auth result: " + data);
        this.authenticated = data;
        if (data === false)
            this.socket.close();

        for (var i = 0; i < this.subscriptions.length; i++){
            this.socket.emit('subscribe', this.subscriptions[i].topic);
        }
    }

    static subscribe(topic, callback)
    {
        var existingSubscription = this.get_subscription(topic);
        if (existingSubscription != null)
        {
            // Already subscribed to this topic, just aa a callback
            var newId = existingSubscription.addCallback(callback);
            if (existingSubscription.lastData)
                callback(newId, existingSubscription.lastData); // Trigger initial update with last data since we aren't subbing on server
            return newId;
        }
        else
        {
            // New subscription topic, let server know
            var subscription = new SocketSubscription(topic);
            var id = subscription.addCallback(callback);
            this.subscriptions.push(subscription)

            if (this.authenticated)
                this.socket.emit('subscribe', topic);
            return id;
        }
    }

    static unsubscribe(callback_id)
    {
        this.subscriptions.forEach(sub =>{
            if(sub.removeCallback(callback_id))
            {
                if(sub.callbacks.length === 0){
                    this.subscriptions = this.subscriptions.filter(item => item !== sub);
                    this.socket.emit('unsubscribe', sub.topic);
                    return;
                }
            }
         });
    }

    static get_subscription(topic)
    {
        for(var i = 0; i < this.subscriptions.length; i++){
            if(this.subscriptions[i].topic === topic)
                return this.subscriptions[i];
        }
        return null;
    }

    static addRequestHandler(request_name, callback){
        this.request_handlers.push({name: request_name, handler: callback});
    }

    static getCurrentRequests()
    {
        this.socket.emit('get_current_requests');
    }

    static respond(request_id, ...data)
    {
        this.socket.emit('response', request_id, data);
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
        this.lastData = null;
    }

    addCallback(callback){
        const id = newId();
        this.callbacks.push({id: id, callback: callback});
        return id;
    }

    removeCallback(id){
        for (var i = 0; i < this.callbacks.length; i++)
        {
            if(this.callbacks[i].id === id)
            {
                this.remove(this.callbacks, this.callbacks[i]);
                return true;
            }
        }
        return false;
    }

    trigger(data){
        this.lastData = data;
        this.callbacks.forEach(cb => cb.callback(cb.id, data));
    }

    remove(arr, element)
    {
      var index = arr.indexOf(element);

      if (index !== -1) {
        arr.splice(index, 1);
      }
    }
}