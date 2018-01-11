(function () {

    angular.module('pi-test').factory('FavoritesFactory', function ($q, $http) {
        var factory = {};
        var favs;

        factory.Add = function(id){
            console.log("Adding fav " + id);
            factory.GetAll().then(function(){
                favs.push(id);
                $http.get("/database/add_favorite?id=" + id);
            });
        }

        factory.Remove = function(id){
            console.log("Remove");
            factory.GetAll().then(function(){
                for(var i = 0 ; i < favs.length; i++){
                    if(favs[i] == id){
                        favs.splice(i, 1);
                        break;
                    }
                }

                $http.get("/database/remove_favorite?id=" + id);
            });
        }

        factory.GetAll = function(){
            var promise = $q.defer();
            if(!favs){
                $http.get("/database/get_favorites").then(function(data){
                    console.log("Favs retrieved");
                    favs = data.data;
                    promise.resolve(data.data);
                });
            }else
            {
                promise.resolve(favs);
            }

            return promise.promise;
        }

        return factory;
    });

})();