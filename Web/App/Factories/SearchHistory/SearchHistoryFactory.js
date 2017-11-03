(function () {

    angular.module('pi-test').factory('SearchHistoryFactory', function () {
        var factory = {};
        var showSearch;
        var movieSearch;

        factory.SetMediaSearch = function(type, keywords, orderBy, localPage, serverPage, scrollOffset){
            if(type == "shows")
                showSearch = { keywords: keywords, orderBy: orderBy, localPage: localPage, serverPage: serverPage, scrollOffset: scrollOffset };
            else
                movieSearch = { keywords: keywords, orderBy: orderBy, localPage: localPage, serverPage: serverPage, scrollOffset: scrollOffset };
        }

        factory.GetMediaSearch = function(type){
            if(type == "shows")
                return showSearch;
            else
                return movieSearch;
        }

        return factory;
    });

})();