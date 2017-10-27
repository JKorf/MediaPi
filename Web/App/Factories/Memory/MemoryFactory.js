(function () {

    angular.module('pi-test').factory('MemoryFactory', function () {
        var factory = {};

        factory.SetValue = function(name, value){
            localStorage.setItem(name, JSON.stringify(value));
        }

        factory.GetValue = function(name){
            var value = localStorage.getItem(name);
            if (value)
                return JSON.parse(value);
            return false;
        }

        factory.Clear = function(){
            localStorage.clear();
        }

        return factory;
    });

})();