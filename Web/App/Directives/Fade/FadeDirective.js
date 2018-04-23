(function () {
    angular.module('pi-test').directive('fade', function () {
        return {
            restrict: 'A',
            link: function ($scope, element, attrs) {
                var vert = attrs["vert"];
                var topOffset = attrs["fadeOffsetTop"];
                var bottomOffset = attrs["fadeOffsetBottom"];
                var leftOffset = attrs["fadeOffsetLeft"];
                var rightOffset = attrs["fadeOffsetRight"];

                if(!topOffset) topOffset = 0;
                if(!bottomOffset) bottomOffset = 0;
                if(!leftOffset) leftOffset = 0;
                if(!rightOffset) rightOffset = 0;

                if (vert === undefined){
                    $(element).after("<div class='fader fader-top' style='top: "+topOffset+"px; left: "+leftOffset+"px; right: "+rightOffset+"px'></div>");
                    $(element).after("<div class='fader fader-bottom' style='bottom: "+bottomOffset+"px; left: "+leftOffset+"px; right: "+rightOffset+"px'></div>");
                    $(element).scroll(function(){
                        if($(element).scrollTop() == 0){
                            $(element).siblings(".fader-top").hide();
                        }else
                        {
                            $(element).siblings(".fader-top").show();
                        }

                        if ($(element)[0].scrollHeight - $(element).scrollTop() == $(element).outerHeight()){
                            $(element).siblings(".fader-bottom").hide();
                        }
                        else
                            $(element).siblings(".fader-bottom").show();
                    });

                    if($(element).scrollHeight <= $(element).outerHeight)
                    {
                        $timeout(function(){
                            $(element).siblings(".fader-bottom").hide();
                        });
                    }
                }
                else{
                    $(element).after("<div class='fader-vert fader-left' style='left: "+leftOffset+"px; top: "+topOffset+"px; bottom: "+bottomOffset+"px;'></div>");
                    $(element).after("<div class='fader-vert fader-right' style='right: "+rightOffset+"px; top: "+topOffset+"px; bottom: "+bottomOffset+"px;'></div>");
                    $(element).scroll(function(){
                        if($(element).scrollLeft() == 0){
                            $(element).siblings(".fader-left").hide();
                        }else
                        {
                            $(element).siblings(".fader-left").show();
                        }

                        if ($(element)[0].scrollWidth - $(element).scrollLeft() == $(element).outerWidth())
                            $(element).siblings(".fader-right").hide();
                        else
                            $(element).siblings(".fader-right").show();
                    });

                    if($(element).scrollWidth <= $(element).outerWidth)
                    {
                        $timeout(function(){
                            $(element).siblings(".fader-right").hide();
                        });
                    }
                }
            }
        };
    });
})();