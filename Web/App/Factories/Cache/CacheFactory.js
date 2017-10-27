(function () {

    angular.module('pi-test').factory('CacheFactory', function ($q, $http) {
        var factory = {};
        var cache = [];

        factory.GetCached = function(url, maxAge){
            for(var i = 0; i < cache.length; i++){
                if(cache[i].url == url){
                    if((new Date().getTime() - cache[i].date.getTime()) / 1000 > maxAge)
                        // If too old, return nothing
                        break;
                    return cache[i].data;
                }
            }
            return false;
        }

        factory.Cache = function(url, data)
        {
            for(var i = 0; i < cache.length; i++){
                if(cache[i].url == url){
                    cache[i].data = data;
                    cache[i].date = new Date();
                    return;
                }
            }

            cache.push({url: url, date: new Date(), data: data});
        }

        factory.Clear = function(){
            cache = [];
        }

        factory.Get = function(url, maxAge)
        {
            var defer = $q.defer();

            var data = factory.GetCached(url, maxAge);
            if(data)
            {
                console.log("From cache: "+ url);
                defer.resolve(data);
            }
            else
            {
                $http.get(url).then(function (response) {
                    factory.Cache(url, response.data);
                    defer.resolve(response.data);
                }, function(err){
                    defer.reject( err);
                });
            }

            return defer.promise;
        }

        return factory;
    });

})();