(function () {

    angular.module('pi-test').factory('FavoritesFactory', function ($q, $http) {
        var factory = {};
        var favs;

        factory.Add = function(id, type, title, image){
            console.log("Adding fav " + id);
            factory.GetAll().then(function(){
                favs.push(createFavorite(id, type, title, image));
                $http.post("/database/add_favorite?id=" + id + "&type=" + type + "&title=" + encodeURIComponent(title) + "&image=" + encodeURIComponent(image));
            });
        }

        factory.Remove = function(id){
            console.log("Remove");
            factory.GetAll().then(function(){
                for(var i = 0 ; i < favs.length; i++){
                    if(favs[i].id == id){
                        favs.splice(i, 1);
                        break;
                    }
                }

                $http.post("/database/remove_favorite?id=" + id);
            });
        }

        factory.GetAll = function(){
            var promise = $q.defer();
            if(!favs){
                $http.get("/database/get_favorites").then(function(data){
                    favs = [];
                    for(var i = 0; i < data.data.length; i++)
                        favs.push(createFavorite(data.data[i][0], data.data[i][2], data.data[i][3], data.data[i][1]));
                    promise.resolve(favs);
                });
            }else
            {
                promise.resolve(favs);
            }

            return promise.promise;
        }

        function createFavorite(id, type, title, image){
            return {
                "id": id,
                "type": type,
                "title": title,
                "image": image
            };
        }

        return factory;
    });

})();