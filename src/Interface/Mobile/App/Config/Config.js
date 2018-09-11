(function () {

    angular.module('pi-test').filter('secondsToTimespan', [function() {
        return function(seconds) {
            var date = new Date(1970, 0, 1);
            date.setSeconds(seconds);
            var hours = date.getHours();
            var minutes = date.getMinutes();
            var seconds = date.getSeconds();
            if (hours > 0)
                minutes += (hours * 60);
            if(minutes < 10)
                minutes = "0"+minutes;
            if(seconds < 10)
                seconds = "0"+seconds;

            return minutes+":"+seconds;
        };
    }]);

     angular.module('pi-test').filter('dateToTimespan', [function() {
        return function(date){
            var time = new Date();
            deltaS = (time.getTime() - new Date(date).getTime()) / 1000;

            if (deltaS < 60)
                return 'just now';
            else if (deltaS < 3600)
                return Math.round((deltaS / 60)) + " mins ago";
            else if (deltaS < 86400)
                return Math.round((deltaS / 3600)) + " hours ago";
            else if (deltaS < 172800)
                return "yesterday";
            else
                return Math.round((deltaS / 86400)) + " days ago"
        }
        }]);

    angular.module('pi-test').filter('secondsToDateTime', [function() {
        return function(seconds) {
            return new Date(1970, 0, 1).setSeconds(seconds);
        };
    }]);

    angular.module('pi-test').filter('startFrom', function() {
        return function(input, start) {
            if(!input)
                return input;

            start = +start; //parse to int
            return input.slice(start);
        }
    });

    angular.module('pi-test').factory('Settings', function() {
        var genres = [
            "action",
            "adventure",
            "animation",
            "comedy",
            "crime",
            "disaster",
            "documentary",
            "drama",
            "eastern",
            "family",
            "fan-film",
            "fantasy",
            "film-noir",
            "history",
            "holiday",
            "horror",
            "indie",
            "music",
            "mystery",
            "none",
            "road",
            "romance",
            "science-fiction",
            "short",
            "sports",
            "sporting-event",
            "suspense",
            "thriller",
            "tv-movie",
            "war",
            "western"
        ];

        var video_extensions = [
            ".mkv",
            ".mp4",
            ".avi",
            ".wmv"
        ]

        var image_extensions = [
            ".png",
            ".jpg",
            ".gif"
        ]

        return {
            genres: genres,
            video_extensions: video_extensions,
            image_extensions: image_extensions
        };
    });
})();