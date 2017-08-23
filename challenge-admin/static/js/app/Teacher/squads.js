/*
@copyright 2015. iZ Hero
Created by FxHarvest LLP
*/
'use strict';

(function(ng){
    /** @ngInject */
    function SquadRootCtrl($scope) {
        $scope.common_ui = {}
    }

    /** @ngInject */
    function SquadListCtrl($scope, $http, $stateParams){
        var self = this;
        $scope.common_ui.selected_mission_name = null;
        this.squads = [];
        var is_tutorial = !!$stateParams.guide;

        this.ui = {
            accounts: 0,
            assigned: 0,
            total_items: 0,
            grid_opts: {
                columnDefs: [
                      {field: '_id', visible: false},
                      {field: 'name', displayName: 'Class Name', width: 250,
                       cellTemplate: '<div class="ui-grid-cell-contents"><a ui-sref="squads.members({code:row.entity.code,name:row.entity.name,is_tutorial:' + is_tutorial + '})" class="btn btn-success btn-sm">{{row.entity.name}}</a></div>'},
                      {field: 'homeroom_teacher_name', displayName: 'Teacher', width: 150},
                      {field: 'code', displayName: 'Code', width: 100},
                      {field: 'dq_points', type: 'number', displayName: 'Total Score', width:100},
                      //{field: 'school', displayName: 'School', width:150},
                      {field: 'grade', displayName: 'Grade', width:150},
                      {field: 'members_count', type: 'number', displayName: 'Students', width:100},
                      //{field: 'donated', displayName: 'Total Donation', width:120},
                      {name: 'add', displayName: 'Add Student', width: 100,
                       cellTemplate: '<div class="ui-grid-cell-contents"><a ui-sref="squads.add_member({code:row.entity.code,name:row.entity.name})" class="btn btn-success btn-sm">Add</a></div>'},
                      {name: 'edit', displayName: 'Edit', width: 60,
                       cellTemplate: '<div class="ui-grid-cell-contents"><a ui-sref="squads.edit({code:row.entity.code,name:row.entity.name})" class="btn btn-primary btn-sm">Edit</a></div>'}
                    ],
                data: [],
                rowHeight: 40
            },
            tutorial: false,
            prepped: false
        };

        $scope.close_tutorial = function () {
            self.ui.tutorial = false;
            // document.getElementById('page-wrapper').style.margin = '0 0 0 220px';
            // document.getElementsByClassName('navbar-static-side')[0].style.display = 'block';
        };

        function getData() {
            $http.get('teachers/accesscode')
                .success(function(res) {
                    self.ui.accounts = res.count || 0;
                    self.ui.assigned = res.assigned || 0;
                });

            $http.get('teachers/squads')
                .success(function(res){
                    if (res.squads) {
                        //self.squads = res.squads;
                        self.ui.grid_opts.data = res.squads;
                        self.ui.total_items = res.squads ? res.squads.length : 0;
                    }
                    /* if (!res.squads || res.squads.length == 0) {
                        document.getElementById('page-wrapper').style.margin = '0';
                        document.getElementsByClassName('navbar-static-side')[0].style.display = 'none';
                        self.ui.tutorial = true;
                    } */
                })
                .error(function(res){
                });
        }

        getData();
    }

    /** @ngInject */
    function SquadCtrl($scope, $http, $state, $stateParams, Session) {
        var self = this;
        $scope.common_ui.selected_mission_name = $stateParams.code ? 'Edit your Class' : 'Create a New Class';
        $scope.ui = {edit: $stateParams.code, is_sub: Session.is_subteacher};

        /* if (angular.isDefined($stateParams.is_tutorial) && $stateParams.is_tutorial === true) {
            document.getElementById('page-wrapper').style.margin = '0';
            document.getElementsByClassName('navbar-static-side')[0].style.display = 'none';
        } */

        this.schools = [];
        this.squad = {
            'name': '',
            'school': Session.school,
            'grade': '',
            'members_count': '',
            'school_others': '',
            'teacher_email': '',
            'teacher_givenname': '',
            'teacher_familyname': ''
        };

        if ($scope.ui.edit) {
            $http.get('teachers/squad/' + $stateParams.code)
                .success(function (res) {
                    self.squad.name = res.name;
                    self.squad.grade = res.grade;
                    if (self.schools.length && !_.contains(self.schools, res.school)) {
                        self.squad.school = 'Others';
                        self.squad.school_others = res.school;
                    } else {
                        self.squad.school = res.school;
                    }
                });
        }

        this.schools_list = function() {
            $http.get('schools/list')
                .success(function (res) {
                    if (res.schools) {
                        self.schools = res.schools;
                    }
                    self.schools.push('Others');

                    if (self.squad.school != '' && self.squad.school != 'Others') {
                        if (!_.contains(self.schools, self.squad.school)) {
                            self.squad.school_others = self.squad.school;
                            self.squad.school = 'Others';
                        }
                    }
                })
                .error(function(res){
                });
        };

        this.cancel = function() {
            $state.transitionTo('squads.list');
        };
        this.save = function(squad) {
            squad.school = self.getschool(squad);
            var action = $stateParams.code ? $http.put : $http.post;
            var url = ($stateParams.code ? 'teachers/squad/' + $stateParams.code : 'teachers/squads');
            action(url, squad)
                .success(function(res) {
                    $state.go('squads.members', {'code': res.code || $stateParams.code, 'name': squad.name,
                                                 'is_tutorial': $stateParams.is_tutorial});
                })
                .error(function(res) {
                    if (!_.contains(self.schools, squad.school)) {
                        squad.school_others = squad.school;
                        squad.school = 'Others';
                    }
                });
        };

        this.getschool = function(squad) {
            if (!angular.isDefined(squad)) {
                squad = self.squad;
            }
            var school = squad.school;
            if (school == 'Others') {
                school = squad.school_others;
            }
            return school;
        }

        this.schools_list();
    }

    /** @ngInject */
    function MemberListCtrl($scope, $http, $stateParams, $state, Session) {
        var self = this;
        $scope.common_ui.selected_mission_name = $stateParams.name;

        this.ui = {
            accounts: 0,
            assigned: 0,
            total_items: 0,
            squad_code: $stateParams.code,
            squad_name: $stateParams.name,
            squads_list: [],
            grid_opts: {
                columnDefs: [
                      {field: '_id', visible: false},
                      {field: 'username', displayName: 'Username', width: 250, enableCellEdit:false},
                      {field: 'genpwd', displayName: 'PW', width: 100, enableCellEdit:false,
                       cellTemplate: '<div class="ui-grid-cell-contents">{{((row.entity.genpwd === "1" || row.entity.genpwd === "") && "********") || row.entity.genpwd}}</div>'},
                      {field: 'password', displayName: 'Change PW', width:150, enableCellEdit:true},

                      {field: 'givenname', displayName: 'Given Name', width:150, enableCellEdit:true},
                      {field: 'familyname', displayName: 'Family Name', width:150, enableCellEdit:true},
                      //{field: 'fullaccess', displayName: 'Type', width: 100, enableCellEdit:false,
                      // cellTemplate: '<div class="ui-grid-cell-contents">{{(row.entity.fullaccess && "Paid") || "Trial"}}</div>'},
                      {field: 'guardiansack', displayName: "Parental's Involvement", width:180, enableCellEdit:false,
                       cellTemplate: '<div class="ui-grid-cell-contents">{{(row.entity.guardiansack && "Yes") || "No"}}</div>'},
                      {field: 'dq_points', type: 'number', displayName: 'Score', width:100, enableCellEdit:false},
                      {field: 'dq_completed', type: 'number', displayName: 'Mission Completed', width: 150, enableCellEdit:false,
                       cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.dq_completed}}/82&nbsp;&nbsp;&nbsp;&nbsp;(<b>{{(row.entity.dq_completed/82*100).toFixed(2)}}%</b>)</div>'},
                      /*{field: 'dq_coins', displayName: 'iZ COINS', width:100, enableCellEdit:false},
                      {field: 'donated', displayName: 'Donated', width:110, enableCellEdit:false}*/
                    ],
                onRegisterApi: function(gridApi) {
                    $scope.gridApi = gridApi;
                    gridApi.edit.on.afterCellEdit($scope, function(rowEntity, colDef, newValue, oldValue) {
                        if (colDef.field == 'status') {
                            if (newValue != oldValue) {
                                if (newValue) {
                                    $http.post('students/izstatus/' + rowEntity._id)
                                        .success(function(res) {
                                        })
                                        .error(function(res) {
                                        });
                                } else {
                                    $http.delete('students/izstatus/' + rowEntity._id)
                                        .success(function(res) {
                                        })
                                        .error(function(res) {
                                        });
                                }
                            }
                        }
                        else if (newValue && newValue != oldValue) {
                            var params = {};
                            // alert(colDef.field);
                            // alert(newValue);
                            if (colDef.field == "password" && newValue.length < 8) {
                                alert('Fail : ' + colDef.field + ' must be at least 8 characters');
                                return;
                            }
                            
                            params[colDef.field] = newValue;

                            $http.put('students/izhero/' + rowEntity._id, params)
                                .success(function(res){
                                    // success
                                    // alert(rowEntity._id);
                                    // console.log(rowEntity._id,params);
                                    // alert(colDef.field);
                                    alert('Success : The ' + colDef.field + ' has been successfully changed.');

                                })
                                .error(function(res) {
                                    // console.log(res);
                                    alert('fail');
                                });
                        }
                    });
                },
                data: []
            },
            tutorial: false
        };

        if (angular.isDefined($stateParams.is_tutorial) && $stateParams.is_tutorial === true) {
            this.ui.tutorial = 1;
            // document.getElementById('page-wrapper').style.margin = '0';
            // document.getElementsByClassName('navbar-static-side')[0].style.display = 'none';
        }

        $scope.close_tutorial = function () {
            self.ui.tutorial = false;
            // document.getElementById('page-wrapper').style.margin = '0 0 0 220px';
            // document.getElementsByClassName('navbar-static-side')[0].style.display = 'block';
        };

        $scope.edit = function(entity) {
            $state.go("squads.member", {id: entity._id});
        };

        function getData() {
            $http.get('teachers/accesscode')
                .success(function(res) {
                    self.ui.accounts = res.count || 0;
                    self.ui.assigned = res.assigned || 0;
                });

            var url = 'students/squad';
            if (angular.isDefined($stateParams.code)) {
                url += '/' + $stateParams.code;
            }
            $http.get(url)
                .success(function(res){
                    self.ui.grid_opts.data = self.ui.grid_opts.data = res.items;
                    self.ui.total_items = res.items ? res.items.length : 0;
                })
                .error(function(res){
                });
        }

        $http.get('teachers/squads')
            .success(function(res){
                if (res.squads) {
                    self.ui.squads_list = res.squads
                }
            });

        $scope.$watch(
            function () {
                return self.ui.squad_code;
            },
            function () {
                if (self.ui.squad_code != $stateParams.code) {
                    var squad_name = '';
                    if (self.ui.squads_list) {
                        for (var i=0; i < self.ui.squads_list.length; i++) {
                            if (self.ui.squad_code == self.ui.squads_list[i].code) {
                                squad_name = self.ui.squads_list[i].name;
                                break;
                            }
                        }
                    }

                    $state.transitionTo('squads.members', {'code': self.ui.squad_code, 'name': squad_name});
                }
            }
        );

        getData();
    }

    /** @ngInject */
    function MemberCtrl($scope, $http, $stateParams, $state) {
        var self = this;
        $scope.common_ui.selected_mission_name = 'Member';
        this.ui = {
            id: $stateParams.id || null,
            squad_code: $stateParams.code || null,
            squad_name: $stateParams.name || null,
        };
        this.izhero = {
            username: '',
            password: '',
            familyname: '',
            givenname: ''
        };
        this.cancel = function() {
            /*if (this.ui.squad_code) {
                $state.transitionTo('squads.members', {'code': self.ui.squad_code, 'name': self.ui.squad_name});
            }*/
            $state.transitionTo('squads.list');
        };
        this.save = function(izhero) {
            if (!self.ui.squad_code) {
                return;
            }
            $http.post('students/squad/' + self.ui.squad_code, izhero)
                .success(function(res) {
                    $state.transitionTo('squads.members', {'code': self.ui.squad_code, 'name': self.ui.squad_name});
                })
                .error(function(res) {
                    //console.log(res);
                });
        };
        this.generate = function(count) {
            if (!self.ui.squad_code) {
                return;
            }
            $http.put('teachers/squad/' + self.ui.squad_code, {'members_count': count})
                .success(function(res) {
                    $state.transitionTo('squads.members', {'code': self.ui.squad_code, 'name': self.ui.squad_name});
                })
                .error(function(res) {
                    //console.log(res);
                });
        };
    }

    /** @ngInject */
    function ProfileCtrl($scope, $http, $state) {
        var self = this;
        this.teach = {
            'familyname': '',
            'givenname': '',
            'contact': '',
        };
        this.pwd = {
            'oldpassword': '',
            'password': '',
            'cfmpassword': ''
        };
        this.ui = {
            msg: '',
            busy: true,
            password: false
        };
        this.data = {
            countries: [],
            schools: [],
            school_others: null
        }

        $http.get('acct/user')
            .success(function(res) {
                self.ui.busy = false;
                if (res) {
                    self.teach.familyname = res.familyname;
                    self.teach.givenname = res.givenname;
                    self.teach.contact = res.contact;
                    self.teach.country = res.country;
                    self.teach.school = res.school;

                    getCountries();
                }
            });

        function getCountries() {
            $http.get('countries/list')
                .success(function (res) {
                    if (res.countries) {
                        self.data.countries = res.countries;
                    }
                });
        }

        function updateSchools() {
            if (self.teach.country) {
                $http.get('/api/izhero/schools', {params: {country: self.teach.country}})
                    .success(function (res) {
                        if (res.schools) {
                            self.data.schools = res.schools;
                            self.data.schools.push('Others');
                            if (!_.contains(self.data.schools, self.teach.school)) {
                                self.data.school_others = self.teach.school;
                                self.teach.school = 'Others';
                            }
                        }
                    });
            }
        }

        $scope.$watch(function () { return self.teach.country; }, updateSchools);

        this.save = function(teach) {
            if (self.ui.busy)   return;
            self.ui.busy = true;

            if (teach.school === 'Others') {
                teach = _.clone(teach);
                teach.school = self.data.school_others;
            }

            $http.put('teachers/update', teach)
                .success(function(res) {
                    self.ui.busy = false;
                    self.ui.msg = 'Saved successfully.';
                })
                .error(function(res) {
                    self.ui.busy = false;
                    //console.log(res);
                });
        };

        this.change_password = function(pwd) {
            if (self.ui.busy)   return;
            self.ui.busy = true;

            $http.put('teachers/update', pwd)
                .success(function(res) {
                    self.ui.busy = false;
                    if (res.success) {
                        self.ui.msg = 'Saved successfully.';
                    } else {
                        self.ui.msg = 'Current Password entered is incorrect.';
                    }
                })
                .error(function(res) {
                    self.ui.busy = false;
                    //console.log(res);
                });
        }

        this.cancel = function() {
            $state.go('squads.list');
        };

        this.password = function() {
            self.ui.password = true;
        };
    }

    function SquadStickerCtrl($scope, $http, $stateParams, $state){
        var bound = false,
            limit = 24,
            pages = [],
            page_index = 0;
        $scope.common_ui.selected_mission_name = ($state.current.data.is_story && 'Stories') || 'Stickers';
        $scope.stickers = [];
        $scope.sticker = null;
        $scope.ui = {
            squad_code: $stateParams.code || null,
            squads_list: [],
            page: 0,
            pages: 1,
            busy: false,
            has_prev: false,
            has_next: false,
            current_index: 0,
            has_page_next: false,
            has_page_prev: false,
            filt: {
                stage: '',
                mission: '',
                sort: ''
            }
        };
        $scope.current = {};

        $scope.open_sticker = function (stker, index) {
            $scope.sticker = stker;
            $scope.ui.has_prev = index > 0;
            $scope.ui.has_next = index < ($scope.stickers.length - 1) || $scope.ui.page < $scope.ui.pages;
            $scope.ui.current_index = index;
            if ($state.current.data.is_story) {
                pages = [{image: stker.cover, caption: stker.title}];
                $scope.current = pages[0];
                pages = pages.concat(stker.pages);
                page_index = 0;
                $scope.ui.has_page_next = (pages.length > 1);
                $scope.ui.has_page_prev = false;
            }
        };
        $scope.prev = function () {
            if ($scope.sticker && $scope.ui.current_index > 0 && $scope.stickers) {
                $scope.ui.current_index -= 1;
                $scope.open_sticker($scope.stickers[$scope.ui.current_index], $scope.ui.current_index);
            }
        };
        $scope.next = function () {
            if ($scope.sticker) {
                if ($scope.ui.current_index < ($scope.stickers.length - 1)) {
                    $scope.ui.current_index += 1;
                    $scope.open_sticker($scope.stickers[$scope.ui.current_index], $scope.ui.current_index);
                } else if ($scope.ui.page < $scope.ui.pages) {
                    var curpage = $scope.ui.page;
                    $scope.getData($scope.ui.squad_code, function () {
                        if ($scope.ui.page > curpage) {
                            $scope.next();
                        }
                    });
                }
            }
        };
        $scope.page_prev = function () {
            if ($scope.sticker && $state.current.data.is_story) {
                if (page_index > 0) {
                    page_index--;
                    $scope.current = pages[page_index];
                    if (page_index <= 0) {
                        $scope.ui.has_page_prev = false;
                    }
                    $scope.ui.has_page_next = true;
                }
            }
        };
        $scope.page_next = function () {
            if ($scope.sticker && $state.current.data.is_story) {
                if (page_index < (pages.length-1)) {
                    page_index++;
                    $scope.current = pages[page_index];
                    if (page_index >= (pages.length-1)) {
                        $scope.ui.has_page_next = false;
                    }
                    $scope.ui.has_page_prev = true;
                }
            }
        };

        $scope.listSquads = function () {
            $scope.ui.squads_list = [];

            $http.get('teachers/squads')
                .success(function(res){
                    if (res.squads) {
                        $scope.ui.squads_list = res.squads;

                        if (!$scope.ui.squad_code) {
                            if ($scope.ui.squads_list.length > 0) {
                                $scope.ui.squad_code = $scope.ui.squads_list[0].code;
                            }
                        } else {
                            var found = false;
                            for (var i = 0; i < $scope.ui.squads_list.length; i++) {
                                if ($scope.ui.squads_list[i].code == $scope.ui.squad_code) {
                                    found = true;
                                    break;
                                }
                            }
                            if (!found) {
                                $scope.ui.squad_code = $scope.ui.squads_list[0].code;
                            }
                        }
                    }
                })
                .error(function(res){
                });
        };
        $scope.$watch('ui.filt.stage', function (val) {
            $scope.ui.filt.mission = '';
            if (!val || val === '0') {
                $scope.ui.list_missions = [];
            } else if (val === '1') {
                $scope.ui.list_missions = [
                    {value: 'izeyes',
                     label: 'iZ EYES'},
                    {value: 'mirror',
                     label: 'Mirror of Truth'},
                    {value: 'childlight',
                     label: 'Children of Light'},
                    {value: 'keeper',
                     label: 'iZ KEEPER'},
                    {value: 'pandora',
                     label: 'Pandora Box'},
                    {value: 'dreamhut',
                     label: 'Dreamhut'},
                    {value: 'tree',
                     label: 'Tree of Respect'},
                    {value: 'lightworld',
                     label: 'Light of the World'},
                    {value: 'izsquad',
                     label: 'iZ SQUAD'},
                    {value: 'star',
                     label: 'Star'}
                ];
            } else if (val === '2') {
                $scope.ui.list_missions = [
                    {value: 'izradar',
                     label: 'iZ RADAR'},
                    {value: 'knowyourenemy',
                     label: 'Know Your Enemy'},
                    {value: 'flameofanger',
                     label: 'Flame of Anger'},
                    {value: 'slowtoanger',
                     label: 'Stay Cool'},
                    {value: 'enails',
                     label: 'E-Nails'},
                    {value: 'three',
                     label: 'Take the 3 Steps'},
                    {value: 'izsquad',
                     label: 'iZ SQUAD MISSION'},
                    {value: 'sense',
                     label: "Sense What's Wrong"},
                    {value: 'izkeeper',
                     label: 'iZ KEEPER'},
                    {value: 'star',
                     label: 'Star'}
                ];
            } else if (val === '3') {
                $scope.ui.list_missions = [
                    {value: 'izcontrol',
                     label: 'iZ CONTROL'},
                    {value: 'knowyourenemy',
                     label: 'Know Your Enemy'},
                    {value: 'childlight',
                     label: 'Children of Light'},
                    {value: 'izkeeper',
                     label: 'iZ KEEPER'},
                    {value: 'discipline',
                     label: 'Power of your Tongue'},
                    {value: 'time',
                     label: 'Time Management'},
                    {value: 'izsquad',
                     label: 'iZ SQUAD MISSION'},
                    {value: 'brutus',
                     label: "Brutus' Mind Games"},
                    {value: 'dungeon',
                     label: "Boolee's Dungeon"},
                    {value: 'contentcritique',
                     label: "Content Critique"},
                    {value: 'contentcritique2',
                     label: "Inappropriate Content"},
                    {value: 'star',
                     label: 'Star'}
                ];
            } else if (val === '4') {
                $scope.ui.list_missions = [
                    {value: 'izprotect',
                     label: 'iZ PROTECT'},
                    {value: 'knowyourenemy',
                     label: 'Know Your Enemy'},
                    {value: 'izkeeper',
                     label: 'iZ KEEPER'},
                    {value: 'childlight',
                     label: 'Children of Light'},
                    {value: 'permission',
                     label: "When in Doubt, Don't Click"},
                    {value: 'personal',
                     label: 'Personal Information'},
                    {value: 'izsquad',
                     label: 'iZ SQUAD MISSION'},
                    {value: 'safety',
                     label: 'Mobile Safety'},
                    {value: 'star',
                     label: 'Star'}
                ];
            } else if (val === '5') {
                $scope.ui.list_missions = [
                    {value: 'izshout',
                     label: 'iZ SHOUT'},
                    {value: 'knowyourenemy',
                     label: 'Know Your Enemy'},
                    {value: 'team',
                     label: 'We are a Team'},
                    {value: 'childlight',
                     label: 'Children of Light'},
                    {value: 'powerpose',
                     label: 'iZ SHOUT Power Pose'},
                    {value: 'speakup',
                     label: 'How to Speak Up'},
                    {value: 'izsquad',
                     label: 'iZ SQUAD MISSION'},
                    {value: 'izkeeper',
                     label: 'iZ KEEPER'},
                    {value: 'star',
                     label: 'Star'}
                ];
            } else if (val === '6') {
                $scope.ui.list_missions = [
                    {value: 'izears',
                     label: 'iZ EARS'},
                    {value: 'knowyourenemy',
                     label: 'Know Your Enemy'},
                    {value: 'childlight',
                     label: 'Children of Light'},
                    {value: 'izkeeper',
                     label: 'iZ KEEPER'},
                    {value: 'express',
                     label: 'Be Kind'},
                    {value: 'hear',
                     label: 'Hear your Inner Voice'},
                    {value: 'izsquad',
                     label: 'iZ SQUAD MISSION'},
                    {value: 'lightworld',
                     label: 'Light of the World'},
                    {value: 'star',
                     label: 'Star'}
                ];
            } else if (val === '7') {
                $scope.ui.list_missions = [
                    {value: 'izteleport',
                     label: 'iZ TELEPORT'},
                    {value: 'knowyourenemy',
                     label: 'Know Your Enemy'},
                    {value: 'childlight',
                     label: 'Children of Light'},
                    {value: 'mediarules',
                     label: 'Set the Media Rules'},
                    {value: 'mediapledge',
                     label: 'My Family Media Pledge'},
                    {value: 'teach',
                     label: 'Teach your Parents'},
                    {value: 'izsquad',
                     label: 'iZ SQUAD MISSION'},
                    {value: 'lightworld',
                     label: 'Light of the World'},
                    {value: 'when',
                     label: 'When to Use iZ TELEPORT'},
                    {value: 'star',
                     label: 'Star'}
                ];
            } else {
                $scope.ui.list_missions = [];
            }
        })

        function detectBtm () {
            var scrollTop = (document.documentElement && document.documentElement.scrollTop) || document.body.scrollTop;
            var isBtm = (window.innerHeight + scrollTop + 200) >= document.body.offsetHeight;
            if (isBtm) {
                $scope.getData($scope.ui.squad_code);
            }
        }

        $scope.getData = function (scode, callback) {
            if (!$scope.ui.busy && $scope.ui.page < $scope.ui.pages) {
                $scope.ui.busy = true;
                var params = {l:limit, p:$scope.ui.page+1}
                if ($state.current.data.removed) {
                    params.removed = true;
                }
                if ($scope.ui.filt.stage || $scope.ui.filt.stage === '0') {
                    params.stage = $scope.ui.filt.stage;
                    if ($scope.ui.filt.mission !== '') {
                        params.mission = $scope.ui.filt.mission;
                    }
                }
                if ($scope.ui.filt.sort !== '1') {
                    params.o = '-_id';
                }
                $http.get(($state.current.data.is_story ? 'stickers/story/squad/' : 'stickers/squad/') + scode, {params:params})
                    .success(function(res){
                        $scope.ui.busy = false;
                        $scope.ui.page += 1;
                        $scope.ui.pages = res.pages;

                        if (res.items) {
                            if (!$state.current.data.is_story) {
                                for (var i = 0; i < res.items.length; i++) {
                                    var stk = res.items[i];
                                    var path = stk.folder ? stk.folder + '/' : ''
                                    path += stk.filename;
                                    stk.path = path;
                                }
                            }

                            $scope.stickers = $scope.stickers.concat(res.items);
                            $scope.ui.total = res.pages === 1 ? res.items.length : res.pages * limit;
                        }

                        if (res.pages > 1 && !bound) {
                            bound = true;
                            angular.element(window).on('scroll', detectBtm);
                        }

                        if (callback && angular.isFunction(callback)) {
                            callback();
                        }
                    })
                    .error(function(res){
                        $scope.ui.busy = false;
                    });
            } else if ($scope.ui.page >= $scope.ui.pages && bound) {
                bound = false;
                angular.element(window).off('scroll');
            }
        };
        $scope.resetData = function () {
            if (!$scope.ui.busy) {
                $scope.ui.page = 0;
                $scope.ui.pages = 1;
                $scope.stickers = [];
                $scope.ui.total = 0;
                if (bound) {
                    bound = false;
                    angular.element(window).off('scroll');
                }
                $scope.getData($scope.ui.squad_code);
            }
        };

        if ($scope.ui.squad_code) {
            $scope.getData($scope.ui.squad_code);
        }

        $scope.$watch('ui.squad_code', function (val, oldVal) {
            if (val && val != oldVal) {
                $scope.ui.page = 0;
                $scope.ui.pages = 1;
                $scope.stickers = [];
                $scope.getData(val);
            }
        });
    }

    /** @ngInject */
    function SquadStickerListCtrl($scope, $http, $stateParams, $state, Session){
        SquadStickerCtrl($scope, $http, $stateParams, $state);

        $scope.ui.squad_code = $stateParams.code || null;

        $scope.remove_sticker = function (stker) {
            $scope.ui.busy = true;
            $http.delete('stickers/squad/' + stker._id)
                .success(function (res) {
                    if (res.success) {
                        if ($scope.sticker) {
                            if ($scope.ui.has_next) {
                                $scope.next();
                            } else if ($scope.ui.has_prev) {
                                $scope.prev();
                            } else {
                                $scope.sticker = null;
                            }

                            if ($scope.sticker) {
                                $scope.ui.current_index -= 1;
                                if ($scope.ui.current_index == 0) {
                                    $scope.ui.has_prev = false;
                                }
                            }
                        }

                        for (var i = 0; i < $scope.stickers.length; i++) {
                            if (stker._id == $scope.stickers[i]._id) {
                                $scope.stickers.splice(i, 1);
                                break;
                            }
                        }
                    }
                });
        };

        $scope.listSquads();

        $scope.open_nominate = function (sticker) {
            if (!$scope.ui.busy) {
                $scope.ui.busy = true;
                $scope.ui.nominate_box = sticker;

                $http.get('../api/gallery/item/' + sticker._id)
                    .success(function (res) {
                        if (res.nominated && res.nominated.length > 0) {
                            for (var i = 0; i < res.nominated.length; i++) {
                                if (Session.username === res.nominated[i].username) {
                                    $scope.ui.nominate_text = res.nominated[i].text;
                                    break;
                                }
                            }
                        }
                        $scope.ui.busy = false;
                    })
                    .error(function (res) {
                        $scope.ui.busy = false;
                    });
            }
        };

        $scope.close_nominate = function () {
            if (!$scope.ui.busy) {
                $scope.ui.nominate_box = null;
                $scope.ui.nominate_text = '';
            }
        };

        $scope.nominate = function (sticker) {
            if (!$scope.ui.busy) {
                $scope.ui.busy = true;

                $http.post('../api/gallery', {sticker: sticker._id, text: $scope.ui.nominate_text})
                    .success(function (res) {
                        $scope.ui.nominate_text = '';
                        $scope.ui.busy = false;
                        $scope.ui.nominate_box = null;
                    })
                    .error(function (res) {
                        $scope.ui.nominate_text = '';
                        $scope.ui.busy = false;
                        $scope.ui.nominate_box = null;
                    });
            }
        };
    }

    /** @ngInject */
    function SquadRStickerListCtrl($scope, $http, $stateParams, $state){
        SquadStickerCtrl($scope, $http, $stateParams, $state);

        $scope.ui.squad_code = $stateParams.code || null;
        $scope.share_sticker = function (stker) {
            $scope.ui.busy = true;
            $http.post('stickers/squad/' + stker._id)
                .success(function (res) {
                    if (res.success) {
                        if ($scope.sticker) {
                            if ($scope.ui.has_next) {
                                $scope.next();
                            } else if ($scope.ui.has_prev) {
                                $scope.prev();
                            } else {
                                $scope.sticker = null;
                            }

                            if ($scope.sticker) {
                                $scope.ui.current_index -= 1;
                                if ($scope.ui.current_index == 0) {
                                    $scope.ui.has_prev = false;
                                }
                            }
                        }

                        for (var i = 0; i < $scope.stickers.length; i++) {
                            if (stker._id == $scope.stickers[i]._id) {
                                $scope.stickers.splice(i, 1);
                                break;
                            }
                        }
                    }
                });
        };

        $scope.listSquads();
    }

    /** @ngInject */
    function SquadStoryListCtrl($scope, $http, $stateParams, $state, Session){
        SquadStickerCtrl($scope, $http, $stateParams, $state);

        $scope.ui.squad_code = $stateParams.code || null;

        $scope.remove_sticker = function (stker) {
            $scope.ui.busy = true;
            $http.delete('stickers/story/squad/' + stker._id)
                .success(function (res) {
                    if (res.success) {
                        if ($scope.sticker) {
                            if ($scope.ui.has_next) {
                                $scope.next();
                            } else if ($scope.ui.has_prev) {
                                $scope.prev();
                            } else {
                                $scope.sticker = null;
                            }

                            if ($scope.sticker) {
                                $scope.ui.current_index -= 1;
                                if ($scope.ui.current_index == 0) {
                                    $scope.ui.has_prev = false;
                                }
                            }
                        }

                        for (var i = 0; i < $scope.stickers.length; i++) {
                            if (stker._id == $scope.stickers[i]._id) {
                                $scope.stickers.splice(i, 1);
                                break;
                            }
                        }
                    }
                });
        };

        $scope.listSquads();

        $scope.open_nominate = function (sticker) {
            if (!$scope.ui.busy) {
                $scope.ui.busy = true;
                $scope.ui.nominate_box = sticker;

                $http.get('../api/gallery/item/' + sticker._id)
                    .success(function (res) {
                        if (res.nominated && res.nominated.length > 0) {
                            for (var i = 0; i < res.nominated.length; i++) {
                                if (Session.username === res.nominated[i].username) {
                                    $scope.ui.nominate_text = res.nominated[i].text;
                                    break;
                                }
                            }
                        }
                        $scope.ui.busy = false;
                    })
                    .error(function (res) {
                        $scope.ui.busy = false;
                    });
            }
        };

        $scope.close_nominate = function () {
            if (!$scope.ui.busy) {
                $scope.ui.nominate_box = null;
                $scope.ui.nominate_text = '';
            }
        };

        $scope.nominate = function (sticker) {
            if (!$scope.ui.busy) {
                $scope.ui.busy = true;

                $http.post('../api/gallery', {story: sticker._id, text: $scope.ui.nominate_text})
                    .success(function (res) {
                        $scope.ui.nominate_text = '';
                        $scope.ui.busy = false;
                        $scope.ui.nominate_box = null;
                    })
                    .error(function (res) {
                        $scope.ui.nominate_text = '';
                        $scope.ui.busy = false;
                        $scope.ui.nominate_box = null;
                    });
            }
        };
    }

    /** @ngInject */
    function SquadRStoryListCtrl($scope, $http, $stateParams, $state){
        SquadStickerCtrl($scope, $http, $stateParams, $state);

        $scope.ui.squad_code = $stateParams.code || null;
        $scope.share_sticker = function (stker) {
            $scope.ui.busy = true;
            $http.post('stickers/story/squad/' + stker._id)
                .success(function (res) {
                    if (res.success) {
                        if ($scope.sticker) {
                            if ($scope.ui.has_next) {
                                $scope.next();
                            } else if ($scope.ui.has_prev) {
                                $scope.prev();
                            } else {
                                $scope.sticker = null;
                            }

                            if ($scope.sticker) {
                                $scope.ui.current_index -= 1;
                                if ($scope.ui.current_index == 0) {
                                    $scope.ui.has_prev = false;
                                }
                            }
                        }

                        for (var i = 0; i < $scope.stickers.length; i++) {
                            if (stker._id == $scope.stickers[i]._id) {
                                $scope.stickers.splice(i, 1);
                                break;
                            }
                        }
                    }
                });
        };

        $scope.listSquads();
    }

    /** @ngInject */
    function NewsListCtrl($scope, $http, $stateParams){
        var self = this;
        $scope.common_ui.selected_mission_name = null;
        $scope.ui = {
            squad_code: $stateParams.code,
            squads_list: []
        };
        this.news = [];

        function listNews () {
            $http.get('news/' + ($scope.ui.squad_code || ''), {params:{o:'-_id'}})
                .success(function (res) {
                    if (res.items) {
                        self.news = res.items;
                    }
                });
        }

        $scope.listSquads = function () {
            $scope.ui.squads_list = [];

            $http.get('teachers/squads')
                .success(function(res){
                    if (res.squads) {
                        $scope.ui.squads_list = res.squads;

                        if (!$scope.ui.squad_code) {
                            if ($scope.ui.squads_list.length > 0) {
                                $scope.ui.squad_code = $scope.ui.squads_list[0].code;
                            }
                        } else {
                            var found = false;
                            for (var i = 0; i < $scope.ui.squads_list.length; i++) {
                                if ($scope.ui.squads_list[i].code == $scope.ui.squad_code) {
                                    found = true;
                                    break;
                                }
                            }
                            if (!found) {
                                $scope.ui.squad_code = $scope.ui.squads_list[0].code;
                            }
                        }
                    }
                })
                .error(function(res){
                });
        };

        $scope.delete_news = function (news) {
            if (news._id && confirm('Are you sure you want to delete this announcement?')) {
                $http.delete('news/item/' + news._id)
                    .success(function (res) {
                        if (res.success && $scope.ui.squads_list.length > 0) {
                            for (var i = 0; i < self.news.length; i++) {
                                if (self.news[i]._id == news._id) {
                                    self.news.splice(i, 1);
                                    break;
                                }
                            }
                        }
                    })
            }
        }

        $scope.listSquads();
        $scope.$watch('ui.squad_code', function (val) {
            listNews();
        });
    }

    /** @ngInject */
    function NewsCtrl($scope, $http, $state, $stateParams, LANG) {
        $scope.data = $stateParams.news || {squad_code: $stateParams.code};
        $scope.ui = {
            is_edit: !!$stateParams.news,
            squads_list: []
        };

        $scope.listSquads = function () {
            $scope.ui.squads_list = [];

            $http.get('teachers/squads')
                .success(function(res){
                    if (res.squads) {
                        $scope.ui.squads_list = res.squads;

                        if (!$scope.data.squad_code) {
                            if ($scope.ui.squads_list.length > 0) {
                                $scope.data.squad_code = $scope.ui.squads_list[0].code;
                            }
                        } else {
                            var found = false;
                            for (var i = 0; i < $scope.ui.squads_list.length; i++) {
                                if ($scope.ui.squads_list[i].code == $scope.data.squad_code) {
                                    found = true;
                                    break;
                                }
                            }
                            if (!found) {
                                $scope.data.squad_code = $scope.ui.squads_list[0].code;
                            }
                        }
                    }
                })
                .error(function(res){
                });
        };

        $scope.listSquads();

        $scope.post_news = function (news) {
            var url = 'news/' + ($scope.data.squad_code || '');
            var method = $http.post;
            if ($scope.data._id) {
                url = 'news/item/' + $scope.data._id;
                method = $http.put;
                if (!$scope.data.until) {
                    delete $scope.data.until;
                }
            }
            news.lang = LANG;
            method(url, news)
                .success(function (res) {
                    $state.go('squads.news');
                });
        };
    }

    ng.controller('SquadRootCtrl', SquadRootCtrl);
    ng.controller('SquadListCtrl', SquadListCtrl);
    ng.controller('SquadCtrl', SquadCtrl);
    ng.controller('MemberListCtrl', MemberListCtrl);
    ng.controller('MemberCtrl', MemberCtrl);
    ng.controller('ProfileCtrl', ProfileCtrl);
    ng.controller('SquadStickerListCtrl', SquadStickerListCtrl);
    ng.controller('SquadRStickerListCtrl', SquadRStickerListCtrl);
    ng.controller('SquadStoryListCtrl', SquadStoryListCtrl);
    ng.controller('SquadRStoryListCtrl', SquadRStoryListCtrl);
    ng.controller('NewsListCtrl', NewsListCtrl);
    ng.controller('NewsCtrl', NewsCtrl);
})(angular.module(APP_MODULE_NAME));