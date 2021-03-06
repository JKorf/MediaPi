﻿(function () {
    angular.module('pi-test').directive('player', function ($rootScope, $http, $state, $filter, $timeout, $interval, $sce, $compile, CacheFactory, RequestFactory, RealtimeFactory, ConfirmationFactory) {
        return {
            restrict: 'E',
            scope: {
            },
            templateUrl: '/App/Directives/Player/player.html',
            link: function ($scope, element, attrs) {
                var playerStates = [];
                playerStates[0] = "Nothing";
                playerStates[1] = "Opening";
                playerStates[2] = "Buffering";
                playerStates[3] = "Playing";
                playerStates[4] = "Paused";
                playerStates[5] = "Ended";

                var playStartTime;
                var playStartOffset;
                var updater;

                var playing = false;
                var media = false;

                $scope.playerState = {state:'Nothing'};
                $rootScope.playerState = 'Nothing';

                Init();

                $rootScope.$on('$stateChangeStart', function(event, toState, toParams, fromState, fromParams, options){
                    SetHeights();
                });

                $scope.settings = function(){
                    $rootScope.openPopup();
                    CacheFactory.Get("/App/Directives/Player/playerSettings.html", 900).then(function(data){
                        $rootScope.setPopupContent("Media settings", false, false, false, data, $scope);
                    });
                }

                $scope.info = function(){
                    $rootScope.openPopup();
                    CacheFactory.Get("/App/Directives/Player/mediaInfo.html", 900).then(function(data){
                        $rootScope.setPopupContent("Media info", false, false, false, data, $scope).then(function(data){}, function(data){
                        });
                    });
                }

                $scope.playPause = function(){
                    $http.post("/player/pause_resume_player");
                    if ($scope.playerState.state == 'Playing')
                        ChangeState('Paused');
                    else
                        ChangeState('Playing');
                }

                $scope.stop = function(){
                    ConfirmationFactory.confirm_stop_current_media().then(function(){
                        $http.post("/player/stop_player");
                        ChangeState("Nothing");
                    });
                }

                $scope.seek = function(obj, amount){
                    console.log("seek " + amount);
                    $http.post("/player/seek?pos=" + amount);
                    ChangeState("Buffering");
                }

                $scope.volChanged = function(obj, amount){
                    console.log("vol " + amount);
                    $http.post("/player/change_volume?vol=" + amount);
                }

                $scope.changeSub = function(sub){
                    console.log("change sub " + sub);
                    $http.post("/player/set_subtitle_id?sub="+sub);
                }

                $scope.changeAudio = function(track){
                    console.log("change audio " + track);
                    $http.post("/player/set_audio_id?track="+track);
                }

                $scope.changeSubtitleOffset = function(obj, amount){
                    console.log("offset " + amount);
                    $http.post("/player/change_subtitle_offset?offset="+ amount);
                }

                $scope.nextImage = function(){
                    console.log("next image");
                    $http.post("/hd/next_image?current_path=" + encodeURIComponent($scope.playerState.path));
                }

                $scope.prevImage = function(){
                    console.log("prev image");
                    $http.post("/hd/prev_image?current_path=" + encodeURIComponent($scope.playerState.path));
                }

                $scope.volumeToolTip = function(value){
                    return value + "%";
                }

                $scope.subTooltip = function(value){
                    return value + "s";
                }

                $scope.seekToolTip = function(value){
                    return $filter("date")($filter("secondsToDateTime")(value), "HH:mm:ss");
                }

                function Init(){
                    $scope.playerState = {}

                    RealtimeFactory.register("PlayerDirective state", "update", function(event, data){
                        if(event == "player")
                            HandlePlayerInfo(data);

                        else if(event == "media")
                            HandleMediaInfo(data);
                    });

                    RealtimeFactory.register("PlayerDirective", "player_event", function(event, data){
                        if(event == "state_change"){
                            state = playerStates[parseInt(data)];
                            ChangeState(state);
                        }
                        if(event == "error"){
                            ChangeState('error');
                            console.log("error");
                        }
                        if(event == "seek"){
                            playStartTime = new Date();
                            playStartOffset = parseInt(data);
                            $scope.playerState.playing_for = parseInt(data);
                            ChangeState("Buffering")
                            console.log("Seek event: " + parseInt(data));
                        }
                        if(event == "volume"){
                            $scope.playerState.volume = parseInt(data);
                        }
                        if(event == "subtitle_id"){
                            $scope.playerState.selected_sub = parseInt(data);
                        }
                        if(event == "subs_done_change"){
                            $scope.playerState.subs_done = data;
                        }
                        if(event == "subtitle_offset"){
                            $scope.playerState.subtitle_delay = parseFloat(data);
                        }
                        if(event == "socket_close"){
                            ChangeState('disconnected');
                        }
                        if(event == "socket_open"){
                            ChangeState(playerStates[0]);
                        }

                        $scope.$apply();
                    });

                    initMediaSession();

                    $rootScope.$on("startPlay", function(event, args){
                        HandlePlayerInfo({
                            state: 1,
                            title: args.title,
                            type: args.type,
                            playing_for: 0,
                            play_time: 0,
                            length: 0
                        });
                    });

                    $rootScope.$on("stopPlay", function(event, args){
                        HandlePlayerInfo({
                            state: 0,
                            title: "",
                            type: "",
                            playing_for: 0,
                            play_time: 0,
                            length: 0
                        });
                    });
                }

                function initMediaSession(){
                    $(document).click(function(){
                        $("#html-player")[0].onplay = function(){
                            $timeout(function(){
                                $("#html-player")[0].pause();
                                $("#html-player")[0].onplay = false;
                             }, 50);
                        };
                        $("#html-player")[0].play();

                        if(playing){
                            setMediaSessionState("playing");
                        }
                        else if(media){
                            setMediaSessionState("paused");
                        }
                        else{
                            setMediaSessionState("none");
                        }
                    });

                    if(navigator.mediaSession)
                    {
                        navigator.mediaSession.setActionHandler("play", function(){ mediaSessionChange(true); });
                        navigator.mediaSession.setActionHandler("pause", function(){ mediaSessionChange(false); });
                    }
                    else
                        console.log("MediaSession not available");
                }

                function setMediaSessionState(state){
                    if(navigator.mediaSession)
                    {
                        if(navigator.mediaSession.playbackState != state){
                            navigator.mediaSession.playbackState = state;
                        }
                    }
                }

                function mediaSessionChange(play){
                    $scope.playPause();
                }

                function updateMediaSessionMetaData(){
                    if(navigator.mediaSession)
                    {
                        if(!$scope.playerState || !media){
                            navigator.mediaSession.metadata = new MediaMetadata({
                              title: "Nothing playing"
                            });
                            return;
                        }

                        var image = $scope.playerState.img;
                        if(!image)
                            image = "/Images/unknown.png";

                        navigator.mediaSession.metadata = new MediaMetadata({
                          title: $scope.playerState.title,
                          artwork: [
                            { src: image }
                          ]
                        });
                    }
                }

                function HandlePlayerInfo(data){
                    data.state = playerStates[parseInt(data.state)];
                    ChangeState(data.state);
                    $scope.playerState = data;

                    updateMediaSessionMetaData();

                    playStartTime = new Date();
                    playStartOffset = $scope.playerState.playing_for;

                    if($scope.playerState.state != 'Nothing' && $scope.playerState.state != 'Buffering')
                    {
                        if(!updater)
                            StartPlayTimer();
                    }
                }

                function StartPlayTimer(){
                    updater = $interval(function(){
                        if(!media){
                            $interval.cancel(updater);
                            updater = false;
                            return;
                        }

                        if(playing){
                            $scope.playerState.playing_for = ((new Date().getTime() - playStartTime.getTime()) / 1000) + playStartOffset;
                            if($scope.playerState.playing_for > $scope.playerState.length && $scope.playerState.length != 0)
                                $scope.playerState.playing_for = $scope.playerState.length;
                        }
                    }, 1000);
                }

                function ChangeState(state){
                    if($scope.playerState.state == state){
                        return;
                    }

                    console.log("Changing state from " + $scope.playerState.state + " to " + state);

                    if(state == 'Nothing' || state == 'Ended' || state == 'error' || state == 'disconnected'){
                        playing = false;
                        media = false;
                        setMediaSessionState("none");
                    }
                    else if(state == 'Paused' || state == 'Buffering' || state == 'Opening')
                    {
                        playing = false;
                        media = true;
                        setMediaSessionState("paused");
                    }
                    else{
                        playing = true;
                        media = true;
                        setMediaSessionState("playing");
                    }

                    $scope.playerState.state = state;
                    $rootScope.playerState = state;
                    SetHeights();
                }

                function SetHeights(){
                    if (media){
                        $("player").addClass("open");
                    }else{
                        $("player").removeClass("open");
                    }
                }

                function HandleMediaInfo(data){
                    $scope.mediaInfo = data;

                    if ($scope.mediaInfo.torrent_state == 1)
                        $scope.mediaInfo.torrent_state = "Initial";
                    if ($scope.mediaInfo.torrent_state == 2)
                        $scope.mediaInfo.torrent_state = "Downloading metadata";
                    if ($scope.mediaInfo.torrent_state == 3)
                        $scope.mediaInfo.torrent_state = "Downloading";
                    if ($scope.mediaInfo.torrent_state == 4)
                        $scope.mediaInfo.torrent_state = "Paused";
                    if ($scope.mediaInfo.torrent_state == 5)
                        $scope.mediaInfo.torrent_state = "Done";
                    if ($scope.mediaInfo.torrent_state == 6)
                        $scope.mediaInfo.torrent_state = "Waiting file selection";
                }
            }
        };
    });
})();