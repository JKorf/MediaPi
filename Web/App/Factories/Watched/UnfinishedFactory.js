(function () {

    angular.module('pi-test').factory('UnfinishedFactory', function ($q, $http, CacheFactory) {
        var factory = {};
        var unfinished;

        factory.GetUnfinished = function(){
            return CacheFactory.Get("/database/get_unfinished_torrents", 60).then(function (response) {
                unfinished = [];
                for(var i = 0; i < response.length; i++){
                    var obj = {
                        name: response[i][1],
                        url: response[i][2],
                        image: response[i][3],
                        position: response[i][4],
                        length: response[i][5],
                        watchedAt: new Date(0)
                    };
                    obj.watchedAt.setUTCSeconds(response[i][6] / 1000)
                    unfinished.push(obj);
                }
                console.log(unfinished);
                return unfinished;
            });
        }

        return factory;
    });

})();