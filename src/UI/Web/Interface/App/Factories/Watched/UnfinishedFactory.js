(function () {

    angular.module('pi-test').factory('UnfinishedFactory', function ($q, $http, CacheFactory) {
        var factory = {};
        var unfinished;

        factory.GetUnfinished = function(){
            return CacheFactory.Get("/database/get_unfinished_items", 60).then(function (response) {
                unfinished = [];
                for(var i = 0; i < response.length; i++){
                    var obj = {
                        name: response[i][1],
                        url: response[i][2],
                        image: response[i][3],
                        position: response[i][4],
                        length: response[i][5],
                        watchedAt: new Date(0),
                        type: response[i][7],
                        mediaFile: response[i][8]
                    };
                    obj.watchedAt.setUTCSeconds(response[i][6] / 1000)
                    if(new Date() - obj.watchedAt > 1000 * 60 * 60 * 24 * 30)
                        factory.Remove(obj);
                    else
                        unfinished.push(obj);
                }
                return unfinished;
            });
        }

        factory.Remove = function(obj){
            unfinished = unfinished.filter(function( item ) {
                return item.url !== obj.url;
            });
            $http.post("/database/remove_unfinished?url=" + encodeURIComponent(obj.url) + "&mediaFile=" + encodeURIComponent(obj.mediaFile));
        }

        return factory;
    });

})();