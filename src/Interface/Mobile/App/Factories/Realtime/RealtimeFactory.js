(function () {

    angular.module('pi-test').factory('RealtimeFactory', function ($interval, $rootScope) {
        var registrations = [];
        var reconnectInterval;
        var socket;
        var wasConnected;

        createWebsocket();
        tryConnect();

        function createWebsocket()
        {
            socket = new WebSocket('ws://' + location.host + '/realtime');
            socket.onopen = function(){
                console.log("Websocket opened");
                wasConnected = true;
                for(var i = 0 ; i < registrations.length; i++){
                    registrations[i].handler('socket_open', "");
                }
            }

            socket.onmessage = function(evnt){
                var data = JSON.parse(evnt.data);

                for(var i = 0 ; i < registrations.length; i++){
                    if(registrations[i].type == data.type){
                        registrations[i].handler(data.event, data.data);
                    }
                }
            }

            socket.onclose = function(){
                if(wasConnected)
                {
                    wasConnected = false;
                    console.log("Websocket closed");
                    for(var i = 0 ; i < registrations.length; i++){
                        registrations[i].handler('socket_close', "");
                    }
                }

                socket = false;
            }

            socket.onerror = function(){
                console.log("error");
            }
        }

        function tryConnect(){
            reconnectInterval = $interval(function(){
                if (socket)
                    return;

                createWebsocket();
            }, 3000);
        }

        var factory = {};

        factory.register = function(name, type, event_handler){
            registrations.push({name: name, type: type, handler: event_handler});
        }

        factory.deregister = function(name){
            registrations = registrations.filter(function( obj ) {
                return obj.name !== name;
            });
        }

        return factory;
    });

})();