(function () {

    angular.module('pi-test').factory('ErrorFactory', function (RealtimeFactory) {
        var errors = [];
        var onNew;

        RealtimeFactory.register("ErrorEventHandler", "error_event", function(event, data){
            if(event != "socket_close" && event != "socket_open")
                errors.push({time: new Date(), type: event, message: data});
                if(onNew)
                    onNew();
            });

        var factory = {};

        factory.getErrors = function(){
            return errors;
        }

        factory.onNewError = function(delegate){
            onNew = delegate;
        }

        return factory;
    });

})();