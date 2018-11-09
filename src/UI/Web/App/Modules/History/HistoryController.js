(function () {

    angular.module('pi-test').controller('HistoryController', function ($scope, $rootScope, $state, HistoryFactory) {

        $scope.history = [];
        $scope.resultLimit = 10;

        var view = $(".view");
        view.scroll(function(){
            if(view[0].scrollHeight - Math.round(view[0].scrollTop) == view[0].offsetHeight)
            {
                $scope.resultLimit += 10;
                $scope.$apply();
            }
        });

        function Init(){

            HistoryFactory.GetWatched().then(function(data){
                for(var i = 0 ; i < data.length; i++){
                    if (data[i].Title == null)
                        continue;

                    if (data[i].Image == null)
                        data[i].Image = undefined;
                    else
                        data[i].Image = decodeURIComponent(data[i].Image);
                }

                $scope.history = data;
            });
        }

        function addLeadingZero(target){
            if(target < 10)
                return "0" + target;
            return target;
        }

        $scope.goToItem = function(item)
        {
            if(item.Type == "Show")
                $state.go("show", { id: item.ImdbId });
            else if(item.Type == "Movie")
                $state.go("movie", { id: item.ImdbId });
            else if (item.Type == "File")
                $state.go("hd", { path: item.URL });
        }

        $scope.removeItem = function(item)
        {
            HistoryFactory.RemoveWatched(item.Id);
            $scope.history.splice($scope.history.indexOf(item), 1);
        }

        Init();

    });

})();