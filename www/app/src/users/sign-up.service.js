(function (window, angular, undefined) {

  'use strict';

  function signUpService($http, $q, BASE_URL, AccountModel) {
    return function (username, email, password, group) {
      var deferred = $q.defer();
      $http.post(BASE_URL + 'sign_up/', {
        username: username,
        email: email,
        password1: password,
        password2: password,
        group: group
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
    .factory('signUpService', ['$http', '$q', 'BASE_URL', 'AccountModel', signUpService]);

})(window, window.angular);