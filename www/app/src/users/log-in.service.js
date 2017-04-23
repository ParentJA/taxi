(function (window, angular, undefined) {

  'use strict';
  
  function logInService($http, $q, BASE_URL, AccountModel) {
    return function (username, password) {
      var deferred = $q.defer();
      $http.post(BASE_URL + 'log_in/', {
        username: username,
        password: password
      }).then(function (response) {
        AccountModel.update(response.data);
        deferred.resolve(AccountModel);
      }, function (response) {
        deferred.reject(response.data);
      });
      return deferred.promise;
    };
  }

  angular.module('taxi')
    .factory('logInService', ['$http', '$q', 'BASE_URL', 'AccountModel', logInService]);

})(window, window.angular);