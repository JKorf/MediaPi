(function () {

    angular.module('pi-test').config(function($stateProvider, $urlRouterProvider) {


        $stateProvider.state('home', {
            url: '/',
            templateUrl: '/App/Modules/Home/home.html',
            cache: false,
            controller: "HomeController",
            pageTitle: "Mediaplayer",
        });

        $stateProvider.state('movies', {
            url: '/media/movies',
            templateUrl: '/App/Modules/Media/medialist.html',
            cache: false,
            controller: "MediaListController",
            pageTitle: "Movies"
        });

        $stateProvider.state('movie', {
            url: '/movie/:id',
            templateUrl: '/App/Modules/Movies/movie.html',
            cache: false,
            controller: "MovieController",
            pageTitle: "Movie"
        });

        $stateProvider.state('shows', {
            url: '/media/shows',
            templateUrl: '/App/Modules/Media/medialist.html',
            cache: false,
            controller: "MediaListController",
            pageTitle: "Shows"
        });

        $stateProvider.state('show', {
            url: '/show/:id',
            templateUrl: '/App/Modules/Shows/show.html',
            cache: false,
            controller: "ShowController",
            pageTitle: "Show"
        });

        $stateProvider.state('direct', {
            url: '/direct',
            templateUrl: '/App/Modules/Direct/direct.html',
            cache: false,
            controller: "DirectController",
            pageTitle: "Direct link"
        });

        $stateProvider.state('hd', {
            url: '/hd/:path',
            templateUrl: '/App/Modules/HD/hd.html',
            cache: false,
            controller: "HDController",
            pageTitle: "Hard drive",
        });

        $stateProvider.state('radio', {
            url: '/radio',
            templateUrl: '/App/Modules/Radio/radio.html',
            cache: false,
            controller: "RadioController",
            pageTitle: "Radios"
        });

        $stateProvider.state('youtube', {
            url: '/youtube',
            templateUrl: '/App/Modules/YouTube/youtube.html',
            cache: false,
            controller: "YouTubeController",
            pageTitle: "YouTube"
        });

        $stateProvider.state('torrents', {
            url: '/torrents',
            templateUrl: '/App/Modules/Torrents/torrents.html',
            cache: false,
            controller: "TorrentsController",
            pageTitle: "Torrents"
        });

        $stateProvider.state('debug', {
            url: '/debug',
            templateUrl: '/App/Modules/Debug/debug.html',
            cache: false,
            controller: "DebugController",
            pageTitle: "Debug"
        });

        $stateProvider.state('settings', {
            url: '/settings',
            templateUrl: '/App/Modules/Settings/settings.html',
            cache: false,
            controller: "SettingsController",
            pageTitle: "Settings"
        });

        $urlRouterProvider.otherwise('/');
    });
})();