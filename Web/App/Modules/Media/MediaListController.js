(function () {

    angular.module('pi-test').controller('MediaListController', function ($scope, $rootScope, $http, $state, $timeout, $stateParams, SearchHistoryFactory, CacheFactory) {
        var initial = true;

        $scope.localPage = 0;
        $scope.serverPage = 0;
        $scope.resultsPerLocalPage = 10;
        $scope.resultsPerServerPage = 50;
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
                 Reset();
            }
        });

        $scope.goToMedia = function (id) {
            if ($scope.mediaType == 'movies')
                $state.go("movie", { id: id });
            else if($scope.mediaType == 'shows')
                $state.go("show", { id: id });
        }

        $scope.searchMedia = function(){
            Reset();
        }

        function Init(){
            var search = SearchHistoryFactory.GetMediaSearch($scope.mediaType);
            if(search)
            {
                $scope.search.keywords = search.keywords;
                $scope.search.orderby = search.orderBy;
                LoadResults(search.localPage, search.serverPage, search.scrollOffset);
            }
            else{
                $timeout(function(){
                    ShowLoadMore();
                });
                LoadResults(1, 1);
            }

            var view = $(".view");
            view.scroll(function(){
                if($scope.loadingMore)
                        return;

                SearchHistoryFactory.SetMediaSearch($scope.mediaType, $scope.search.keywords, $scope.search.orderby, $scope.serverPage, $scope.localPage, view[0].scrollTop);

                var moreServerResults = true;
                if($scope.mediaList.length % $scope.resultsPerServerPage != 0){
                    moreServerResults = false;
                }

                if(view[0].scrollHeight - view[0].scrollTop == view[0].offsetHeight)
                {
                    var localResults = $scope.localPage * $scope.resultsPerLocalPage;
                    var serverResults =  $scope.serverPage * $scope.resultsPerServerPage;
                    console.log(localResults +" - " + serverResults);

                    if(localResults == serverResults){
                        if(!moreServerResults)
                            return;

                        LoadResults($scope.serverPage + 1, $scope.localPage + 1);
                    }

                    if(localResults < serverResults){
                        if($scope.localPage * $scope.resultsPerLocalPage > $scope.mediaList.length)
                            return;

                        LoadResults($scope.serverPage, $scope.localPage + 1);
                    }

                    $scope.$apply();
                }
            });
        }

        function Reset()
        {
            $scope.serverPage = 0;
            $scope.localPage = 0;
            $scope.done = false;
            $scope.loadingMore = false;
            $scope.mediaList = [];
            initial = true;
            $timeout(function(){
                ShowLoadMore();
            });
            LoadResults(1,1);
        }

        function ShowLoadMore(){
            $(".media-more-loader").show();
            $(".media-more").hide();
        }

        function HideLoadMore(scrollOffset){
            $timeout(function(){
                $(".media-more-loader").hide();
                $(".media-more").show();
                $scope.loadingMore = false;
                $(".media-box").removeClass("hide");
                if(scrollOffset){
                    $timeout(function(){
                        $(".view")[0].scrollTop = parseInt(scrollOffset);
                    });
                }
            }, 1000);
        }

        function LoadResults(serverPage, localPage, scrollOffset)
        {
            ShowLoadMore();
            $scope.loadingMore = true;
            SearchHistoryFactory.SetMediaSearch($scope.mediaType, $scope.search.keywords, $scope.search.orderby, serverPage, localPage, $(".view")[0].scrollTop);
            $(".media-search-box input").blur();
            if(serverPage > $scope.serverPage)
            {
                $scope.done = false;
                // Load more from server
                console.log(GetUri(serverPage));
                $scope.promise = CacheFactory.Get(GetUri(serverPage), 900).then(function (response) {
                    $scope.mediaList.push.apply($scope.mediaList, response);
                    $scope.serverPage = serverPage;
                    $scope.localPage = localPage;

                    initial = false;
                    $scope.done = true;

                    HideLoadMore(scrollOffset);
                }, function (err) {
                    $scope.done = true;
                    console.log(err);
                });
            }
            else
            {
                $scope.localPage = localPage;
                HideLoadMore();
            }
        }

        function GetUri(page)
        {
            var base = '/movies/get_movies';
            if ($scope.mediaType == 'shows')
                base = '/shows/get_shows';

            if(initial)
                base += "_all"

            return base + '?page='+ page +'&orderby=' + encodeURIComponent($scope.search.orderby) + '&keywords=' + encodeURIComponent($scope.search.keywords);
        }
    });

})();