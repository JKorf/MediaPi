(function () {

    angular.module('pi-test').controller('HDController', function ($scope, $rootScope, $http, $state, $stateParams, $location, $timeout, Settings, HistoryFactory, ConfirmationFactory) {
        var initial = true;

        $scope.current = { drive: "/", path: "" };;
        $scope.drives = [];
        $scope.filterSettingsOpen = false;
        $scope.showVideos = true;
        $scope.showSubtitles = false;
        $scope.showImages = false;
        $scope.watchedFiles = [];
        $scope.referencedFile = "";

        $(document).mouseup(function (e)
        {
            var target = $(e.target);
            if($(".hd-filter").has(target) && !target.is($(".hd-filter")) && !target.is($(".hd-filter svg"))){
                $scope.filterSettingsOpen = false;
                $scope.$apply();
            }
        });

        Init();

        $scope.filterFiles = function(file){
            var lowerStr = (file + "").toLowerCase();
            if (Settings.video_extensions.some(function(v) { return lowerStr.indexOf(v) >= 0; })) {
                return $scope.showVideos;
            }
            else if (Settings.image_extensions.some(function(v) { return lowerStr.indexOf(v) >= 0; })) {
                return $scope.showImages;
            }
            else if (lowerStr.endsWith(".srt"))
                return $scope.showSubtitles;
        }

        $timeout(function(){
            var listener = $rootScope.$on('$locationChangeStart', function(event, newUrl, oldUrl) {
                if($scope.current.path != $scope.current.drive)
                {
                    event.preventDefault();
                    console.log(event);
                    $scope.directoryUp();
                }
            });

            $scope.$on('$destroy', function(){
                listener();
            });
        });

        $scope.fileHasBeenWatched = function(file){
            var path = concatPath($scope.current.path, file)
            return $.grep($scope.watchedFiles, function(item){
                return item.URL == path;
            }).length != 0;
        }

        $scope.startsWith = function (actual) {
            var lowerStr = (actual + "").toLowerCase();
            if (Settings.video_extensions.some(function(v) { return lowerStr.indexOf(v) >= 0; })) {
                return true;
            }

            if (Settings.image_extensions.some(function(v) { return lowerStr.indexOf(v) >= 0; })) {
                return true;
            }

            if (lowerStr.endsWith(".srt"))
                return true;

            return false;
        }

        $scope.isImage = function(actual){
            var lowerStr = (actual + "").toLowerCase();
            if (Settings.image_extensions.some(function(v) { return lowerStr.indexOf(v) >= 0; })) {
                return true;
            }
            return false;
        }

        $scope.isMovie = function(actual){
            var lowerStr = (actual + "").toLowerCase();
            if (Settings.video_extensions.some(function(v) { return lowerStr.indexOf(v) >= 0; })) {
                return true;
            }
            return false;
        }

        $scope.isSubtitle = function(actual){
            var lowerStr = (actual + "").toLowerCase();
            if (lowerStr.endsWith(".srt"))
                    return true;
        }

        $scope.changeDirectory = function(relativePath){
            GetDirectory(concatPath($scope.current.path, relativePath));
        }

        $scope.directoryUp = function(){
            $scope.referencedFile = "";
            var lastIndex = $scope.current.path.lastIndexOf('/');
            if (lastIndex == 2 || lastIndex == 0)
                GetDirectory("");
            else
            {
                if(lastIndex == $scope.current.path.length - 1){
                    $scope.current.path = $scope.current.path.substr(0, lastIndex);
                    $scope.directoryUp();
                }
                else
                    GetDirectory($scope.current.path.substr(0, lastIndex));
            }
        }

        $scope.playFile = function(file){
            if ($scope.isSubtitle(file))
                return $scope.addSubtitle(file);

            if ($scope.isImage(file))
                return $scope.playImage(file);

            if ($scope.isMovie(file))
                return $scope.playMovie(file);
        }

        $scope.addSubtitle = function(file){
            if($rootScope.playerState == "Nothing")
                return;

            ConfirmationFactory.confirm_subtitle().then(function(){
                var path = concatPath($scope.current.path, file);
                $http.post("/player/set_subtitle_file?file=" + encodeURIComponent(path));
            });
        }

        $scope.playImage = function(file){
            ConfirmationFactory.confirm_play().then(function(){
                var path = concatPath($scope.current.path, file);
                $http.post("/hd/play_file?filename=" + encodeURIComponent(file)+"&path=" + encodeURIComponent(path));
            });
        }

        $scope.playMovie = function(file){
            ConfirmationFactory.confirm_play().then(function(){
                $rootScope.$broadcast("startPlay", {title: file, type: "File"});

                var path = concatPath($scope.current.path, file);
                $http.post("/hd/play_file?filename=" + encodeURIComponent(file)+"&path=" + encodeURIComponent(path));

                $timeout(function(){
                    HistoryFactory.GetWatched().then(function(data){
                        $scope.watchedFiles = data;
                    });
                }, 2000);
            });
        }

        function Init(){
            GetDrives();

            $scope.$watch("current.drive", function(newv, oldv){
                if(newv != oldv){
                    if(initial)
                    {
                        initial = false;
                        return;
                    }
                    GetDirectory("");
                }
            });
        }

        function GetDrives(){
            $http.get("/hd/drives").then(function (response) {
                $scope.drives = response.data;
                console.log($scope.drives);

                if ($scope.drives.length > 0){
                    $scope.current.drive = $scope.drives[0];
                }

                if ($stateParams.path.length > 0){
                    var lastIndex = $stateParams.path.lastIndexOf('/');
                    $scope.referencedFile = $stateParams.path.substr(lastIndex + 1);

                    if (lastIndex == 2 || lastIndex == 0)
                       GetDirectory("");
                    else{
                        var path = $stateParams.path;
                        if(path.indexOf(".") != -1)
                            path = path.substring(0, $stateParams.path.lastIndexOf("/") + 1);

                        GetDirectory(path);
                   }
                }
                else
                    GetDirectory("");
            }, function (err) {
                 console.log("error: " + err);
            });
        }

        function GetDirectory(path){
            if(path == "" || path == "/")
                path = $scope.current.drive

            $scope.current.path = path;
            console.log("Getting dir for " + path);
            $scope.promise = $http.get("/hd/directory?path=" + encodeURIComponent(path)).then(function (response) {
                $scope.filestructure = response.data;
                HistoryFactory.GetWatched().then(function(data){
                    $scope.watchedFiles = data;
                });
                if($scope.referencedFile.length > 0){
                    $timeout(function(){
                        var titles = $(".hd-file-title");
                        for(var i = 0; i < titles.length; i++){
                            if(titles[i].innerText == $scope.referencedFile){
                                var offsetTop = $(titles[i]).parent()[0].offsetTop;
                                $(".view").animate({scrollTop:offsetTop - ($(".view").height() / 2)}, 200);
                            }
                        }
                    });
                }
            }, function (err) {
                console.log("error: " + err);
            });
        }

        function concatPath(part1, part2){
            var splitter = "/";
            if (part1.endsWith("/"))
                splitter = ""
            return part1 + splitter + part2;
        }
    });

})();