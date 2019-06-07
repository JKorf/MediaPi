let moviesSearch = {term: "", page: 1, order: "Trending"};
let showSearch = {term: "", page: 1, order: "Trending"};
let youTubeSearch = {term: "", page: 1, order: "Video"};
let torrentsSearch = {term: "", category: "TV"};

export function updateMoviesSearch(term, page, order){
    moviesSearch.term = term;
    moviesSearch.page = page;
    moviesSearch.order = order;
}

export function getMoviesSearch(){
    return moviesSearch;
}

export function updateShowsSearch(term, page, order){
    showSearch.term = term;
    showSearch.page = page;
    showSearch.order = order;
}

export function getShowsSearch(){
    return showSearch;
}

export function updateYouTubeSearch(term, page, order){
    youTubeSearch.term = term;
    youTubeSearch.page = page;
    youTubeSearch.order = order;
}

export function getYouTubeSearch(){
    return youTubeSearch;
}

export function updateTorrentsSearch(term, category){
    torrentsSearch.term = term;
    torrentsSearch.category = category;
}

export function getTorrentsSearch(){
    return torrentsSearch;
}