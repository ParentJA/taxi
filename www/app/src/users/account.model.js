(function (window, angular, undefined) {

  'use strict';

  function AccountModel() {
    var user = {};

    this.clear = function clear() {
      user = {};
    };

    this.getUser = function getUser() {
      return user;
    };

    this.hasUser = function hasUser() {
      return !_.isEmpty(user);
    };

    this.isRider = function isRider() {
      return _.first(user.groups) === 'rider';
    };

    this.isDriver = function isDriver() {
      return _.first(user.groups) === 'driver';
    };

    this.update = function update(dict) {
      user = dict;
    };
  }

  angular.module('taxi')
    .service("AccountModel", [AccountModel]);

})(window, window.angular);