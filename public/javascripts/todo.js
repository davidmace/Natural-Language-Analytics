angular.module('editorApp', [])
  .controller('EditorController', ['$scope', function($scope) {
    $scope.openfiles = [
      {name:'main.html', nameeditable:false, 'text':'yo'},
      {name:'main.css', nameeditable:false, 'text':'yoA'},
      {name:'main.js', nameeditable:false, 'text':'yoB'}
    ];
    $scope.curtab=0;
 
    $scope.closetab = function(i) {
      $scope.openfiles.splice(i, 1);
    };

    $scope.addtab = function() {
      $scope.openfiles.push({name:'new', nameeditable:false, 'text':'newYay'});
    };

    $scope.editname = function(i) {
      $scope.openfiles[i].nameeditable=true;
    };

    $scope.blurtab = function(i) {
      $scope.openfiles[i].nameeditable=false;
    };

    $scope.choosetab = function(i) {
      $scope.curtab=i;
    };

    $scope.gettext = function() {
      return $scope.openfiles[$scope.curtab].text;
    };
 
  }]);