let moviesSearch = {term: "", page: 1, order: "Trending"};
let showSearch = {term: "", page: 1, order: "Trending"};
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

export function updateTorrentsSearch(term, category){
    torrentsSearch.term = term;
    torrentsSearch.category = category;
}

export function getTorrentsSearch(){
    return torrentsSearch;
}