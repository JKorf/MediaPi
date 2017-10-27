(function () {

    angular.module('pi-test').controller('MediaListController', function ($scope, $rootScope, $http, $state, $timeout, $stateParams, SearchHistoryFactory, CacheFactory) {
        var loadedUntilPage = 0;
        var showPerResult = 16;
        var serverResult = 50;
        var initial = true;

        $scope.showUntil = 0;
        $scope.done = false;
        $scope.loadingMore = false;
        $scope.mediaList = [];
        $scope.mediaType = $state.current.name;

        if ($scope.mediaType == 'movies')
            $scope.searchoptions = ["trending", "rating", "last added", "title"];
        else if ($scope.mediaType == 'shows')
            $scope.searchoptions = ["trending", "rating", "updated", "name"];

        $scope.search = {
            keywords: "",
            orderby: $scope.searchoptions[0]
        };

        Init();

        $scope.$watch('search.orderby', function(newv, oldv){
            if(oldv && newv && oldv != newv){
                $scope.done = false;
                loadedUntilPage = 0;
                $scope.showUntil = 0;
                $scope.mediaList = [];
                initial = true;
                LoadMore();
            }
        });

        $scope.goToMedia = function (id) {
            if ($scope.mediaType == 'movies')
                $state.go("movie", { id: id });
            else if($scope.mediaType == 'shows')
                $state.go("show", { id: id });
        }

        $scope.searchMedia = function(){
            $scope.done = false;
            loadedUntilPage = 0;
            $scope.showUntil = 0;
            $scope.mediaList = [];
            initial = true;

            ShowLoadMore();
            LoadMore();
        }

        function Init(){
            var search = SearchHistoryFactory.GetMediaSearch();
            if(search)
            {
                $scope.search.keywords = search.keywords;
                $scope.search.orderby = search.orderBy;
            }

            var view = $(".view");
            view.scroll(function(){
                if($scope.loadingMore)
                        return;

                if(view[0].scrollHeight - view[0].scrollTop == view[0].offsetHeight)
                {
                    console.log("Scrolled to bot")
                    $scope.loadingMore = true;

                    if($scope.showUntil == $scope.mediaList.length)
                        return;

                    if($scope.showUntil + showPerResult > $scope.mediaList.length)
                    {
                        if($scope.mediaList.length % serverResult != 0)
                        {
                            $scope.showUntil = $scope.mediaList.length;
                            $scope.$apply();
                            ShowLoadMore();
                            HideLoadMore();
                        }
                        else{
                            console.log("Loading new page")
                            $scope.done = false;
                            ShowLoadMore();
                            LoadMore();
                        }
                    }
                    else if ($scope.mediaList.length > $scope.showUntil){
                        $scope.showUntil = Math.min($scope.showUntil + showPerResult, $scope.mediaList.length);
                        $scope.$apply();
                        ShowLoadMore();
                        HideLoadMore();
                    }
                }
            });

            $timeout(function(){
                ShowLoadMore();
            });
            LoadMore();
        }

        function ShowLoadMore(){
            $(".media-more-loader").show();
            $(".media-more").hide();
        }

        function HideLoadMore(){
            $timeout(function(){
                $(".media-more-loader").hide();
                $(".media-more").show();

                $scope.loadingMore = false;
                $(".media-box").removeClass("hide");
            }, 1000);
        }

        function LoadMore() {
            SearchHistoryFactory.SetMediaSearch($scope.search.keywords, $scope.search.orderby);
            loadedUntilPage += 1;

            var base = '/movies/get_movies';
            if ($scope.mediaType == 'shows')
                base = '/shows/get_shows';

            var baseUri = base + '?page='+ loadedUntilPage +'&orderby=' + encodeURIComponent($scope.search.orderby) + '&keywords=' + encodeURIComponent($scope.search.keywords);

            console.log("Getting new media list");

            $(".media-search-box input").blur();

            $scope.promise = CacheFactory.Get(baseUri, 900).then(function (response) {
                $scope.mediaList.push.apply($scope.mediaList, response);
                $scope.showUntil = Math.min($scope.showUntil + showPerResult, $scope.mediaList.length);
                                        console.log($scope.showUntil);

                $scope.done = true;
                HideLoadMore();
            }, function (err) {
                $scope.done = true;
                console.log(err);
            });
        }
    });

})();