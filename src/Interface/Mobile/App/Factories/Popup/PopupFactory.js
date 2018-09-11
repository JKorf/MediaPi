(function () {

    angular.module('pi-test').factory('PopupFactory', function ($rootScope, $http, $window, $compile, $q, $timeout, RealtimeFactory, CacheFactory, HistoryFactory) {

         RealtimeFactory.register("IndexController", "request", function(event, data){
            if(event == "media_selection")
                OpenMediaSelection(data);

            if(event == "next_episode"){
                OpenSelectNextEpisode(data);
            }

            if(event == "media_selection_close")
                $rootScope.closePopup();
        });

        function OpenSelectNextEpisode(data){
            var open = true;
            $rootScope.openPopup();
            $rootScope.setPopupContent("Continue playing", true, true, true, "Found next episode, do you want to continue with season " + data.season + ", episode " + data.episode + "?", $rootScope).then(function(action){
                open = false;
                if(data.type == "File"){
                    $rootScope.$broadcast("startPlay", {title: data.filename, type: "File"});
                    $http.post("/hd/play_file?path=" + encodeURIComponent(data.path) + "&filename=" + encodeURIComponent(data.title));
                    HistoryFactory.AddWatchedFile(data.title, data.path, new Date());
                    $rootScope.$broadcast("startPlay", {title: data.title, type: "File"});
                }
                else{
                    $http.post("/movies/play_continue?type=torrent&url=" + encodeURIComponent(data.path) + "&title=" + encodeURIComponent(data.title) +"&image="+encodeURIComponent(data.img)+"&position=0&mediaFile=" + encodeURIComponent(data.media_file));
                    $rootScope.$broadcast("startPlay", {title: data.title, type: "Show"});
                    HistoryFactory.LastWatchedShow().then(function(show){
                         HistoryFactory.AddWatchedShow(show.ImdbId, show.Title, data.img, parseInt(data.season), parseInt(data.episode), new Date());
                    });
                }
            }, function(action){
                console.log(action);
            });

            $timeout(function(){
                if(open)
                    $rootScope.closePopup();
            }, 1000 * 60 * 30);

        }

        function OpenMediaSelection(data)
        {
        console.log(data);
            var scope =  $rootScope.$new(true);
            scope.selectedFile = false;
            scope.files = data;

            scope.addLeadingZero = function(target){
                if(target < 10)
                    return "0" + target;
                return target;
            }

            scope.selectFile = function(file){
                scope.selectedFile = file.path;
                console.log(file);
            }

            scope.seasons = {};
            for(var i = 0; i < scope.files.length; i++){
                if(!scope.seasons[scope.files[i].season + ""])
                    scope.seasons[scope.files[i].season + ""] = [];
                scope.seasons[scope.files[i].season + ""].push(scope.files[i]);
            }

            $rootScope.openPopup();
            CacheFactory.Get("/App/Modules/Index/mediaselection.html", 900).then(function(data){
                $rootScope.setPopupContent("Select file to play", true, true, true, data, scope, function() { return scope.selectedFile; }).then(function(action){
                    console.log(action);
                    $http.post("/player/select_file?path=" + encodeURIComponent(scope.selectedFile) + "&watchedAt=" + new Date());
                }, function(action){
                    console.log(action);
                    if (action != "invalid"){
                        $http.post("/player/stop_player");
                        $rootScope.$broadcast("stopPlay");
                    }
                });
            });
        }

        $rootScope.openPopup = function(){
            $rootScope.popupTitle = "";
            $rootScope.popupCancel = false;
            $rootScope.popupOk = false;
            $rootScope.modal = false;

            $(".popup").remove();
            $(".popup-background").remove();
            $("body").append($compile("<div class='popup-background' ng-click='backgroundClick()'></div>")($rootScope));
            $("body").append($compile(
                '<div class="popup">' +
                    '<div class="popup-title">{{popupTitle}}</div>' +
                    '<div class="popup-close" ng-click="popupCancelClick()">X</div>' +
                    '<div class="popup-content" ng-class="{buttonsshown: popupCancel || popupOk}"></div>' +
                    '<div class="popup-buttons">' +
                        '<div class="popup-button-cancel popup-button" ng-click="popupCancelClick()" ng-if="popupCancel" ng-class="{singlebutton: !popupOk}">Cancel</div>' +
                        '<div class="popup-button-ok popup-button" ng-click="popupOkClick()" ng-if="popupOk" ng-class="{singlebutton: !popupCancel}">Ok</div>' +
                    '</div>' +
                '</div>')($rootScope));
        }


        angular.element($window).bind('resize', function(){
            $(".popup-content").css("max-height", $window.innerHeight - 240 + "px");
        });

        $rootScope.closePopup = function(){
            $(".popup").remove();
            $(".popup-background").remove();

            if($rootScope.currentPromise && $rootScope.currentPromise.promise.$$state.status == 0)
                $rootScope.currentPromise.reject("invalid");
        }

        $rootScope.setPopupContent = function(title, showCancel, showOk, modal, content, scope, canConfirmFunc){
            $rootScope.currentPromise = $q.defer();

            $timeout(function(){
                $rootScope.popupTitle = title;
                $rootScope.popupCancel = showCancel;
                $rootScope.popupOk = showOk;
                $rootScope.modal = modal
                $rootScope.popupCancelClick = function(){
                    $(".popup").remove();
                    $(".popup-background").remove();
                    $rootScope.currentPromise.reject("cancel");
                }
                $rootScope.popupOkClick = function(){
                    if (canConfirmFunc && !canConfirmFunc())
                        return;

                    $(".popup").remove();
                    $(".popup-background").remove();
                    $rootScope.currentPromise.resolve("ok");
                }
                $rootScope.backgroundClick = function(){
                    if(!$rootScope.modal){
                        $(".popup").remove();
                        $(".popup-background").remove();
                        $rootScope.currentPromise.reject("cancel");
                    }
                }

                $(".popup-content").append(content)
                $compile($(".popup-content")[0])(scope);

                $timeout(function(){
                    $(".popup-content").css("max-height", $window.innerHeight - 240 + "px");
                });
            });

            return $rootScope.currentPromise.promise;
        }

        return {};
    });

})();