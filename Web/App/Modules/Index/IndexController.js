(function () {

    angular.module('pi-test').controller('IndexController', function ($scope, $rootScope, $q, $http, $state, $timeout, $compile, CacheFactory, RealtimeFactory) {
        $http.defaults.headers.post["Content-Type"] = "application/x-www-form-urlencoded";

        RealtimeFactory.register("IndexController", "request", function(event, data){
            console.log(data);
            if(event == "media_selection")
            {
                $scope.selectedFile = false;
                $scope.files = data;
                for(var i = 0; i < $scope.files.length; i++){
                    var file = $scope.files[i];
                    if(file.season != 0 && file.episode != 0){
                        var s = file.season + "";
                        var e = file.episode + "";
                        if(s.length == 1)
                            s = "0" + s;
                        if(e.length == 1)
                            e = "0" + e;
                        file.se = "S" + s + "E" + e;
                    }
                }
                $rootScope.openPopup();
                CacheFactory.Get("/App/Modules/Index/mediaselection.html", 900).then(function(data){
                    $rootScope.setPopupContent("Select file to play", false, true, true, data, $scope, function() { return $scope.selectedFile; }).then(function(){
                        $http.post("/player/select_file?path=" + encodeURIComponent($scope.selectedFile));
                    }, function(){
                        $http.post("/player/stop_player");
                    });
                });
            }
        });

        $scope.selectFile = function(file){
            $scope.selectedFile = file.path;
            console.log(file);
        }

        $rootScope.$watch('playerState', function (newv, oldv){
            SetHeight(newv);
        });

        $rootScope.$on('$stateChangeSuccess', function(event, toState, toParams, fromState, fromParams, options){
            $timeout(function(){
                SetHeight($rootScope.playerState);
            }, 1);
        });

        $rootScope.openMenu = function(event){
            if($(event.target).parent(".slider").length == 0)
                $rootScope.$broadcast('openMenu');
        }

        $rootScope.closeMenu = function(event){
            if($(event.target).parent(".slider").length == 0)
                $rootScope.$broadcast('closeMenu');
        }

        $rootScope.openPopup = function(){
            $scope.popupTitle = "";
            $scope.popupCancel = false;
            $scope.popupOk = false;
            $scope.modal = false;

            $(".popup").remove();
            $(".popup-background").remove();
            $("body").append($compile("<div class='popup-background' ng-click='backgroundClick()'></div>")($scope));
            $("body").append($compile(
                '<div class="popup">' +
                    '<div class="popup-title">{{popupTitle}}</div>' +
                    '<div class="popup-close" ng-click="popupCancelClick()">X</div>' +
                    '<div class="popup-content" ng-class="{buttonsshown: popupCancel || popupOk}"></div>' +
                    '<div class="popup-buttons">' +
                        '<div class="popup-button-cancel popup-button" ng-click="popupCancelClick()" ng-if="popupCancel" ng-class="{singlebutton: !popupOk}">Cancel</div>' +
                        '<div class="popup-button-ok popup-button" ng-click="popupOkClick()" ng-if="popupOk" ng-class="{singlebutton: !popupCancel}">Ok</div>' +
                    '</div>' +
                '</div>')($scope));
        }

        $rootScope.setPopupContent = function(title, showCancel, showOk, modal, content, scope, canConfirmFunc){
            var defer = $q.defer();

            $timeout(function(){
                $scope.popupTitle = title;
                $scope.popupCancel = showCancel;
                $scope.popupOk = showOk;
                $scope.modal = modal
                $scope.popupCancelClick = function(){
                    $(".popup").remove();
                    $(".popup-background").remove();
                    defer.reject();
                }
                $scope.popupOkClick = function(){
                    if (canConfirmFunc && !canConfirmFunc())
                        return;
                    $(".popup").remove();
                    $(".popup-background").remove();
                    defer.resolve();
                }
                $scope.backgroundClick = function(){
                    if(!$scope.modal){
                        $(".popup").remove();
                        $(".popup-background").remove();
                        defer.reject();
                    }
                }

                $(".popup-content").append(content)
                $compile($(".popup-content")[0])(scope);
            });

            return defer.promise;
        }

        function SetHeight(playerState){
            $(".view").removeClass("player-closed");
            $(".view").removeClass("player-visible");

            if (playerState && playerState != 'Nothing' && playerState != 'disconnected'){
                $(".view").addClass("player-visible");
                $("menu").addClass("player-open");
            }else{
                $(".view").addClass("player-closed");
                $("menu").removeClass("player-open");
            }
        }

        function Init(){
            $rootScope.pageTitle = "Mediaplayer";
            $http.get("/util/startup").then(function (response) {
                $rootScope.pageTitle = response.data.instance_name;
            });
        }

        Init();
    });
})();