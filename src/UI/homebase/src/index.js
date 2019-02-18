import React from 'react';
import ReactDOM from 'react-dom';
import App from './App.js';


//axios.interceptors.request.use(request => {
//  console.log('Starting Request', request)
//  return request
//})
//
//axios.interceptors.response.use(response => {
//  console.log('Response:', response)
//  return response
//})

ReactDOM.render(<App />, document.getElementById('root'));

Array.prototype.remove = function(element) {
  var index = this.indexOf(element);

  if (index !== -1) {
    this.splice(index, 1);
  }
}
