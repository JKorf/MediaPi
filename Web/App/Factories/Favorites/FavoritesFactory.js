(function () {

    angular.module('pi-test').factory('FavoritesFactory', function (MemoryFactory) {
        var factory = {};
        var favs;

        factory.Add = function(id){
            if(!favs){
                factory.GetAll();
            }

            favs.push({id: id, addedAt: new Date()});
            MemoryFactory.SetValue("Favorites", favs);
        }

        factory.Remove = function(id){
            if(!favs){
                factory.GetAll();
            }

            for(var i = 0 ; i < favs.length; i++){
                if(favs[i].id == id){
                    favs.splice(i, 1);
                    MemoryFactory.SetValue("Favorites", favs);
                    return;
                }
            }

        }

        factory.GetAll = function(){
            if(!favs){
                favs = MemoryFactory.GetValue("Favorites");
                if(!favs)
                    favs = [];
            }

            return favs;
        }

        factory.IsFavorite = function(id){
            if(!favs)
                factory.GetAll();

            for(var i = 0 ; i < favs.length; i++){
                if(favs[i].id == id)
                    return true;
            }
            return false;
        }

        return factory;
    });

})();