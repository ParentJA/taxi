(function (window, angular, undefined) {

  'use strict';

  function logOutService($http, $q, BASE_URL, AccountModel) {
    return function () {
      var deferred = $q.defer();
      var user = AccountModel.getUser();
      $http.post(BASE_URL + 'log_out/', null, {
        headers: {
          Authorization: 'Token ' + user.auth_token
        }
      }).finally(function () {
        AccountModel.clear();
        deferred.resolve(AccountModel);
      });
      return deferred.promise;
    };
  }

  angular.module('taxi')
    .factory('logOutService', ['$http', '$q', 'BASE_URL', 'AccountModel', logOutService]);

})(window, window.angular);