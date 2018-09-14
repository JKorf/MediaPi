(function () {

    angular.module('pi-test').factory('SVGFactory', function ($rootScope, $timeout) {

        function checkSVGs(image){
             // init global cache object and assign local var
            var cache = this.svgCache = this.svgCache || {};

            // define function to replace single svg
            var replaceSVG = function( data ){
                // get img and attributes
                var $img = jQuery(image),
                    attributes = $img.prop("attributes");

                // Clone the SVG tag, ignore the rest
                var $svg = jQuery(data).find('svg').clone();

                // Remove any invalid XML tags as per http://validator.w3.org
                $svg = $svg.removeAttr('xmlns:a');

                // Loop through IMG attributes and add them to SVG
                jQuery.each(attributes, function() {
                    $svg.attr(this.name, this.value);
                });

                // Replace image with new SVG
                $img.replaceWith($svg);
            }

            // loop all svgs

            // get URL from this SVG
            var imgURL = jQuery(image).attr('src');

            // if not cached, make new AJAX request
            if ( ! cache[imgURL] ){
                cache[imgURL] = jQuery.get(imgURL).promise();
            }

            // when we have SVG data, replace img with data
            cache[imgURL].done( replaceSVG.bind(image) );
        }

        return { check: checkSVGs };
    });

})();