(function () {

    angular.module('pi-test').factory('UnfinishedFactory', function ($q, $http) {
        var factory = {};
        var unfinished;

        factory.GetUnfinished = function(){
            var promise = $q.defer();
            if(!unfinished){
                $http.get("/database/get_unfinished_torrents").then(function(data){
                    unfinished = [];
                    for(var i = 0; i < data.data.length; i++){
                        var obj = {
                            name: data.data[i][1],
                            url: data.data[i][2],
                            image: data.data[i][3],
                            position: data.data[i][4],
                            length: data.data[i][5],
                            watchedAt: new Date(0)
                        };
                        obj.watchedAt.setUTCSeconds(data.data[i][6] / 1000)
                        unfinished.push(obj);
                    }
                    console.log(unfinished);
                    promise.resolve(unfinished);
                });
            }else
            {
                promise.resolve(unfinished);
            }

            return promise.promise;
        }

        return factory;
    });

})();