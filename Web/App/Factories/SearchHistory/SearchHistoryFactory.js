(function () {

    angular.module('pi-test').factory('SearchHistoryFactory', function () {
        var factory = {};
        var mediaSearch;

        factory.SetMediaSearch = function(keywords, orderBy){
            mediaSearch = { keywords: keywords, orderBy: orderBy };
        }

        factory.GetMediaSearch = function(){
            return mediaSearch;
        }

        return factory;
    });

})();