var version = 'v1::'

self.addEventListener("install", function(event) {

});

self.addEventListener("fetch", function(event) {
    event.respondWith(
        caches.match(event.request).then(function(cached)
        {
            var networked = fetch(event.request).then(fetchedFromNetwork, networkError);
            if(IsImage() || IsPage())
                return cached || networked;
            else
                return networked || cached;

            function fetchedFromNetwork(response) {
                if(event.request.method != 'GET')
                    return response;

                var cacheCopy = response.clone();

                caches.open(version + 'resources').then(function add(cache) {
                    cache.put(event.request, cacheCopy);
                });

                return response;
            }

            function networkError () {
                return caches.match(event.request);
            }
      })
  );

  function IsImage(){
    if (!event.request.url.endsWith('.png') && !event.request.url.endsWith('.gif') && !event.request.url.endsWith('.jpg') && !event.request.url.endsWith('.jpeg'))
        return false;
    return true;
  }

  function IsPage(){
    if (!event.request.url.endsWith('.html') && !event.request.url.endsWith('.js') && !event.request.url.endsWith('.css'))
        return false;
    return true;
  }
});

self.addEventListener("activate", function(event) {
  event.waitUntil(
    caches
      .keys()
      .then(function (keys) {
        return Promise.all(
          keys
            .filter(function (key) {
              return !key.startsWith(version);
            })
            .map(function (key) {
              return caches.delete(key);
            })
        );
      })
      .then(function() {
      })
  );
});