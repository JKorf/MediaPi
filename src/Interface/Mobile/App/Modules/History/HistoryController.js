(function () {

    angular.module('pi-test').controller('HistoryController', function ($scope, $rootScope, $state, HistoryFactory) {

        $scope.history = [];

        function Init(){

            HistoryFactory.GetWatched().then(function(data){
                for(var i = 0 ; i < data.length; i++){
                    if (data[i].Title == null)
                        continue;

                    if (data[i].Image == null)
                        data[i].Image = undefined;
                    else
                        data[i].Image = decodeURIComponent(data[i].Image);

                    if (!data[i].Title.endsWith("]") && data[i].Season){
                        data[i].Title += " [S" + addLeadingZero(data[i].Season) + "E" + addLeadingZero(data[i].Episode) + "]";
                    }
                }

                $scope.history = data;
            });
        }

        function addLeadingZero(target){
            if(target < 10)
                return "0" + target;
            return target;
        }

        $scope.goToItem = function(item){

            if(item.Type == "Show")
            {
                $state.go("show", { id: item.ImdbId });
            }
            else if (item.Type == "File")
            {
                $state.go("hd", { path: item.URL });
            }
        }

        Init();

    });

})();