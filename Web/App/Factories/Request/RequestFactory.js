(function () {

    angular.module('pi-test').factory('RequestFactory', function ($interval, $http) {
        var factory = {};
        var requesting = [];

        factory.StartRequesting = function(url, interval, dataOut, errorOut, shouldExecuteTest){
            var requestingObject = {url: url, interval: interval, requestOut: false, dataOut: dataOut, errorOut: errorOut, shouldExecuteTest: shouldExecuteTest};
            requesting.push(requestingObject);

            executeRequest(url, true);
            requestingObject.intervalObject = $interval(function(){
                executeRequest(url, false);
            }, interval);

            return requestingObject.intervalObject
        }

        factory.InvokeNow = function(interval){
            var requestingObject = $.grep(requesting, function(e){ return e.intervalObject == interval; })[0];
            executeRequest(requestingObject.url, true);
        }

        factory.StopRequesting = function(interval){
            $interval.cancel(interval);
            for(var i = 0; i < requesting.length; i++)
            {
                if(requesting[i].intervalObject == interval){
                    requesting.splice(i, 1);
                    break;
                }
            }
        }

        function executeRequest(url, ignorePreCheck){
            var requestingObject = $.grep(requesting, function(e){ return e.url == url; })[0];

            if(requestingObject.requestOut)
                return;

            if(!ignorePreCheck)
                if(requestingObject.shouldExecuteTest && !requestingObject.shouldExecuteTest())
                    return;

            requestingObject.requestOut = true;
            $http.get(url).then(function(response){
                requestingObject.requestOut = false;
                requestingObject.dataOut(response);
            }, function(err){
                requestingObject.requestOut = false;
                requestingObject.errorOut(err);
            });
        }

        return factory;
    });

})();