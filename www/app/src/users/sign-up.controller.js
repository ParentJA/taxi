(function (window, angular, undefined) {

  'use strict';

  function SignUpController($state, signUpService) {
    var vm = this;

    vm.error = {};
    vm.form = '';
    vm.group = 'rider';
    vm.password = null;
    vm.passwordAgain = null;
    vm.username = null;

    vm.hasError = function hasError() {
      return !_.isEmpty(vm.error);
    };

    vm.onSubmit = function onSubmit() {
      signUpService(vm.username, vm.password, vm.group).then(function () {
        $state.go('log_in');
      }, function (response) {
        vm.error = response;
        vm.password = null;
        vm.passwordAgain = null;
      });
    };

    vm.passwordsMatch = function passwordsMatch() {
      return (!_.isEmpty(vm.password) && vm.password === vm.passwordAgain);
    };
  }

  angular.module('taxi')
    .controller('SignUpController', ['$state', 'signUpService', SignUpController]);

})(window, window.angular);