(function (window, angular, undefined) {

  'use strict';

  function TripResource($http, $q, BASE_URL, AccountModel, Trip) {
    this.list = function list() {
      var deferred = $q.defer();
      var user = AccountModel.getUser();

      $http.get(BASE_URL + 'trip/', {
        headers: {
          Authorization: 'Token ' + user.auth_token
        }
      }).then(function (response) {
        Trip.updateList(response.data);
        deferred.resolve(Trip);
      }, function (response) {
        console.error('Failed to get trips.');
        deferred.reject(response);
      });

      return deferred.promise;
    };

    this.create = function create(trip) {
      var deferred = $q.defer();
      var user = AccountModel.getUser();

      $http.post(BASE_URL + 'trip/', trip, {
        headers: {
          Authorization: 'Token ' + user.auth_token
        }
      }).then(function (response) {
        Trip.updateDict(response.data);
        deferred.resolve(Trip);
      }, function (response) {
        console.error('Failed to create trip.');
        deferred.reject(response);
      });

      return deferred.promise;
    };

    this.retrieve = function retrieve(nk) {
      var deferred = $q.defer();
      var user = AccountModel.getUser();

      $http.get(BASE_URL + 'trip/' + nk + '/', {
        headers: {
          Authorization: 'Token ' + user.auth_token
        }
      }).then(function (response) {
        Trip.updateDict(response.data);
        deferred.resolve(Trip);
      }, function (response) {
        console.error('Failed to update trip with NK ' + nk + '.');
        deferred.reject(response);
      });

      return deferred.promise;
    };
    
    this.update = function update(nk, trip) {
      var deferred = $q.defer();
      var user = AccountModel.getUser();

      $http.put(BASE_URL + 'trip/' + nk + '/', trip, {
        headers: {
          Authorization: 'Token ' + user.auth_token
        }
      }).then(function () {
        Trip.removeDict(nk);
        deferred.resolve(Trip);
      }, function (response) {
        console.error('Failed to update trip with NK ' + nk + '.');
        deferred.reject(response);
      });

      return deferred.promise;
    }
  }

  angular.module('taxi')
    .service('TripResource', ['$http', '$q', 'BASE_URL', 'AccountModel', 'Trip', TripResource]);

})(window, window.angular);