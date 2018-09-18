(function () {
    angular.module('pi-test').directive('player', function ($rootScope, $http, $state, $filter, $timeout, $interval, $sce, $compile, CacheFactory, RequestFactory, RealtimeFactory, ConfirmationFactory) {
        return {
            restrict: 'E',
            scope: {
            },
            templateUrl: '/App/Directives/Player/player.html',
            link: function ($scope, element, attrs) {
                var playerStates = [];
                var request = false;

                playerStates[0] = "Nothing";
                playerStates[1] = "Opening";
                playerStates[2] = "Buffering";
                playerStates[3] = "Playing";
                playerStates[4] = "Paused";
                playerStates[5] = "Ended";

                var playStartTime;
                var playStartOffset;
                var updater;
                var playerInterval;
                var playerInvokeInterval;

                var playing = false;
                var media = false;

                $scope.playerState = {state:'disconnected'};

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
                    RequestMediaInfo();
                    var mediaInfoInterval = $interval(function(){ RequestMediaInfo(); }, 2000);
                    CacheFactory.Get("/App/Directives/Player/mediaInfo.html", 900).then(function(data){
                        $rootScope.setPopupContent("Media info", false, false, false, data, $scope).then(function(data){}, function(data){
                            $interval.cancel(mediaInfoInterval);
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

                $scope.seek = function(){
                    console.log("seek " + $scope.playerState.playing_for);
                    $http.post("/player/seek?pos=" + $scope.playerState.playing_for);
                    ChangeState("Buffering");
                }

                $scope.volChanged = function(){
                    console.log("vol " + $scope.playerState.volume);
                    $http.post("/player/change_volume?vol=" + $scope.playerState.volume);
                }

                $scope.changeSub = function(sub){
                    console.log("change sub " + sub);
                    $http.post("/player/set_subtitle_id?sub="+sub);
                }

                $scope.changeAudio = function(track){
                    console.log("change audio " + track);
                    $http.post("/player/set_audio_id?track="+track);
                }

                $scope.changeSubtitleOffset = function(){
                    console.log("offset " + $scope.playerState.subtitle_delay);
                    $http.post("/player/change_subtitle_offset?offset="+ $scope.playerState.subtitle_delay);
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

                    RealtimeFactory.register("PlayerDirective", "player_event", function(event, data){
                        if(event == "state_change"){
                            state = playerStates[parseInt(data)];
                            ChangeState(state);
                            if(!playerInvokeInterval)
                            {
                                playerInvokeInterval = $timeout(function(){
                                    // Invoke again after 2 seconds to make sure we got the latest state because invoke wont trigger if already busy
                                    RequestFactory.InvokeNow(playerInterval);
                                    playerInvokeInterval = false;
                                }, 2000);
                            }
                        }
                        if(event == "error"){
                            ChangeState('error');
                            console.log("error");
                            RequestFactory.InvokeNow(playerInterval);
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
                            RequestFactory.InvokeNow(playerInterval);
                        }
                        if(event == "subtitle_offset"){
                            $scope.playerState.subtitle_delay = parseFloat(data);
                        }
                        if(event == "socket_close"){
                            ChangeState('disconnected');
                        }
                        if(event == "socket_open"){
                            ChangeState(playerStates[0]);
                            RequestFactory.InvokeNow(playerInterval);
                        }

                        $scope.$apply();
                    });

                    initMediaSession();

                    playerInterval = RequestFactory.StartRequesting("/util/player_state", 5000, handlePlayerInfo, handlePlayerError, shouldRequestPlayerState)

                    $scope.$on("$destroy", function(){
                        RequestFactory.StopRequesting(playerInterval);
                    });

                    $rootScope.$on("startPlay", function(event, args){
                        handlePlayerInfo({data: {
                            state: 1,
                            title: args.title,
                            type: args.type,
                            playing_for: 0,
                            play_time: 0,
                            length: 0
                        }});
                    });

                    $rootScope.$on("stopPlay", function(event, args){
                        handlePlayerInfo({data: {
                            state: 0,
                            title: "",
                            type: "",
                            playing_for: 0,
                            play_time: 0,
                            length: 0
                        }});
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

                function shouldRequestPlayerState(){
                    if(!media)
                        return false;
                    return true;
                }

                function handlePlayerInfo(response){
                    response.data.state = playerStates[parseInt(response.data.state)];
                    ChangeState(response.data.state);
                    $scope.playerState = response.data;

                    updateMediaSessionMetaData();

                    playStartTime = new Date();
                    playStartOffset = $scope.playerState.playing_for;

                    if($scope.playerState.state != 'Nothing' && $scope.playerState.state != 'Buffering')
                    {
                        StartPlayTimer();
                    }
                }

                function handlePlayerError(err){
                    console.log(err);
                    ChangeState('disconnected');
                }

                function StartPlayTimer(){
                    if(updater)
                        $interval.cancel(updater);

                    updater = $interval(function(){
                        if(!media){
                            $interval.cancel(updater);
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

                function RequestMediaInfo(){
                    if(request)
                        return;

                    request = $http.get("/util/media_info").then(function(response){
                        request = false;
                        $scope.mediaInfo = response.data;

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
                    }, function(er){
                        request = false;
                        $scope.mediaInfo = false;
                    });
                }
            }
        };
    });
})();