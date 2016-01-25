'use strict';

$(function() {
    var TableModel = Backbone.Model.extend({
        defaults: {
            year: 2015,
            row_labels: [
                'Individual Income Tax Liability Change',
                'Payroll Tax Liability Change',
                'Combined Payroll and Individual Income Tax Liability Change'
            ]
        },

        initialize: function() {
            this.buildExtraColumnKeys();
            this.divideCellValues();
            this.columnVisibility();
        },

        buildExtraColumnKeys: function() {
            _.each(this.get('cols'), function(col) {
                col.divisor_label = '';
                if (col.divisor === 1000) {
                    col.divisor_label += 'Thousands';
                } else if (col.divisor === 1000000) {
                    col.divisor_label += 'Millions';
                } else if (col.divisor === 1000000000) {
                    col.divisor_label += 'Billions';
                }
                col.divisor_label += col.units ? col.divisor_label ? ' of ' + col.units : col.units : '';
                col.label_val = col.label.toString().toLowerCase().split(" ").join("-");
            });
        },

        divideCellValues: function() {
            var that = this;
            var i = 0;
            _.each(this.get('rows'), function(row) {
                var j = 0;
                _.each(row.cells, function(cell) {
                    if (_.isEmpty(cell.year_values)) {
                        that.get('rows')[i]['cells'][j]['tot_value'] = that.numberWithCommas((parseFloat(cell.value / cell.format.divisor)).toFixed(cell.format.decimals));
                    } else {
                        _.each(_.keys(cell.year_values), function(year) {
                            that.get('rows')[i]['cells'][j]['year_values'][year] = that.numberWithCommas((parseFloat(cell.year_values[year] / cell.format.divisor)).toFixed(cell.format.decimals));
                        });
                    }
                    j++;
                });
                i++;
            });
        },

        numberWithCommas: function(x) {
            var parts = x.toString().split(".");
            parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
            return parts.join(".") === "NaN" ? 0 : parts.join(".");
        },

        columnVisibility: function() {
            _.map(this.get('cols').slice(0, 10), function(col) {
                col.show = true;
                return col;
            });
        }
    });

    var SelectedTableModel = Backbone.Model.extend({
        defaults: {
            difference: false,
            plan:'X',
            payroll_tax: true,
            income_tax: false,
            income: 'expanded',
            grouping: 'bin'
        },

        reference: function() {
            var grouping = '_' + this.get('grouping');
            if (this.get('difference') && !(this.get('payroll_tax') || this.get('income_tax'))) {
                return false;
            }
            var tax = (this.get('payroll_tax')) ? ((this.get('income_tax')) ? 'c' : 'p') : '';
            var table = (this.get('difference') ? tax + 'df' : 'm' + this.get('plan')) + '_' + this.get('grouping')
            return table;
        },

        rowLabels: function() {
            if (this.get('grouping') == 'bin') {
                return [
                    'Less than 10',
                    '10-20',
                    '20-30',
                    '30-40',
                    '40-50',
                    '50-75',
                    '75-100',
                    '100-200',
                    '200-500',
                    '500-1000',
                    '1000+',
                    'All'
                ];
            } else if (this.get('grouping') == 'dec') {
                return [
                    '0-10%',
                    '10-20%',
                    '20-30%',
                    '30-40%',
                    '40-50%',
                    '50-60%',
                    '60-70%',
                    '70-80%',
                    '80-90%',
                    '90-100%',
                    'All'
                ];
            }
        }
    });

    var TablesCollection = Backbone.Collection.extend({
        model: TableModel
    });

    var TableView = Backbone.View.extend({
        template: _.template('\
            <div class="panel panel-default">\
                <div class="panel-body" style="overflow: scroll">\
                    <table class="table table-striped" style="width:100%">\
                        <thead>\
                            <tr>\
                                <th class="text-center" colspan="<%= model.get("cols").length + 1 %>"><h1><%= model.get("label").toUpperCase() %><% if (model.get("reference") !== "fiscal_tots") { %> (<%= model.get("year") %>)<% } %></h1></th>\
                            </tr>\
                            <tr>\
                                <th></th>\
                                <% _.each(model.get("cols"), function(col) { %>\
                                <%   if (col.show) { %>\
                                <th class="text-center"><strong><%= col.label %></strong></th>\
                                <%   } %>\
                                <% }) %>\
                            </tr>\
                        </thead>\
                        <tbody>\
                            <tr>\
                                <td></td>\
                                <% _.each(model.get("cols"), function(col) { %>\
                                <%   if (col.show) { %>\
                                <td class="text-center"><small class="text-muted"><%= col.divisor_label %></small></td>\
                                <%   } %>\
                                <% }) %>\
                            </tr>\
                            <% _.each(model.get("rows"), function(row, idx) { %>\
                            <tr>\
                                <td class="text-center"><strong><%= model.get("row_labels")[idx] %></strong></td>\
                                <% _.each(row.cells, function(cell, idx) { %>\
                                <%   if (model.get("cols")[idx].show) { %>\
                                <td class="text-center"><% if (cell["tot_value"]) { %><%= cell["tot_value"] %><% } else { %><%= cell["year_values"][model.get("year")] %><% } %></td>\
                                <%   } %>\
                                <% }) %>\
                            </tr>\
                            <% }) %>\
                        </tbody>\
                    </table>\
                </div>\
            </div>\
        '),

        render: function() {
            this.$el.html(this.template({ model: this.model }));
        }
    })

    var TableSelectView = Backbone.View.extend({
        el: '<div class="panel panel-default"></div>',
        template: _.template('\
              <div class="panel-heading">\
                <h3 class="panel-title">Build Table</h3>\
              </div>\
              <div class="panel-body">\
                <div class="row">\
                    <div class="col-md-6">\
                        <h1 class="text-center">For Year: </h1>\
                    </div>\
                    <div class="col-md-6">\
                        <h1 class="text-center">\
                            <div class="dropdown dropdown-select dropdown-inline data-switch">\
                              <a class="dropdown-toggle" type="button" id="years" data-toggle="dropdown" aria-expanded="true">\
                                <%= result_years[0] %>\
                                <span class="caret"></span>\
                              </a>\
                              <ul class="dropdown-menu" role="menu" aria-labelledby="years">\
                                <% _.each(result_years, function(year) { %>\
                                <li role="presentation">\
                                  <a role="menuitem" tabindex="-1" href="#" data-year="<%= year %>">\
                                    <%= year %>\
                                  </a>\
                                </li>\
                                <% }) %>\
                              </ul>\
                            </div>\
                        </h1>\
                    </div>\
                </div>\
                <br>\
                <br>\
                <ul class="nav nav-pills nav-justified">\
                  <li class="active" data-difference="false"><a href="#">Diagnostic</a></li>\
                  <li data-difference="true"><a href="#">Difference</a></li>\
                </ul>\
                <br>\
                <br>\
                <ul id="plan" class="nav nav-pills nav-justified">\
                  <li class="active" data-plan="X"><a href="#">Base</a></li>\
                  <li data-plan="Y"><a href="#">User</a></li>\
                </ul>\
                <ul id="tax" class="nav nav-pills nav-justified" style="display:none">\
                  <li class="active" data-payrolltax="false"><a href="#">Payroll</a></li>\
                  <li><h1 class="text-center" style="margin:0">+</h1></li>\
                  <li data-incometax="true"><a href="#">Income</a></li>\
                </ul>\
                <br>\
                <br>\
                <ul class="nav nav-pills nav-justified">\
                  <li class="active" data-income="expanded"><a href="#">Expanded Income</a></li>\
                  <li class="disabled" data-income="adjusted"><a href="#" disabled>Adjusted Income</a></li>\
                </ul>\
                <br>\
                <br>\
                <ul class="nav nav-pills nav-justified">\
                  <li class="active" data-grouping="bin"><a href="#">Income Bins</a></li>\
                  <li data-grouping="dec"><a href="#">Income Decimals</a></li>\
                </ul>\
              </div>\
            </div>'),

        events: {
            'click [data-year]': function(e) {
                e.preventDefault();
                this.collection.each(function(table) {
                    table.set('year', $(e.currentTarget).data('year'), {
                        silent: true
                    });
                });
                this.$el.find('#years').html($(e.currentTarget).data('year') + ' <span class="caret"></span>');
                tables.trigger('update');
            },

            'click [data-payrolltax]': function(e) {
                var $el = $(e.currentTarget);
                var payrolltax = $el.data('payrolltax');
                this.model.set('payroll_tax', payrolltax);
                $el.data('payrolltax', !payrolltax);
                $el.toggleClass('active');
            },
            'click [data-incometax]': function(e) {
                var $el = $(e.currentTarget);
                var incometax = $el.data('incometax')
                this.model.set('income_tax', incometax);
                $el.data('incometax', !incometax);
                $el.toggleClass('active');
            },
            'click [data-difference]': function(e) {
                var $el = $(e.currentTarget);
                this.model.set('difference', $el.data('difference'));
                this.$el.find('[data-difference]').removeClass('active');
                $el.addClass('active');
            },
            'click [data-difference="true"]': function(e) {
                var $el = $(e.currentTarget);
                this.$el.find('#tax').show();
                this.$el.find('#plan').hide();
            },
            'click [data-difference="false"]': function(e) {
                var $el = $(e.currentTarget);
                this.$el.find('#tax').hide();
                this.$el.find('#plan').show();
            },
            'click [data-grouping]': function(e) {
                var $el = $(e.currentTarget);
                this.model.set('grouping', $el.data('grouping'));
                this.$el.find('[data-grouping]').removeClass('active');
                $el.addClass('active');
            },
            'click [data-plan]': function(e) {
                var $el = $(e.currentTarget);
                this.model.set('plan', $el.data('plan'));
                this.$el.find('[data-plan]').removeClass('active');
                $el.addClass('active');
            },
            'click .nav-pills li a': function(e) {
                e.preventDefault();
            }
        },

        initialize: function(options) {
            this.resultYears = options.resultYears;
        },

        render: function() {
            this.$el.html(this.template({ result_years: this.resultYears }));
        }

    });

    var ColumnSelectView = Backbone.View.extend({
        template: _.template('\
            <div class="panel panel-default">\
                <div class="panel-heading">\
                    <h3 class="panel-title">\
                        Select Columns\
                        <div class="pull-right">\
                            <label>\
                                <input type="checkbox" id="select-all" <% if (_.every(this.model.get("cols"), function(col) { return col.show; })) { %> checked <% } %>> Select All\
                            </label>\
                        </div>\
                    </h3>\
                </div>\
                <div class="panel-body">\
                    <div class="block-grid-md-3 block-grid-sm-3 block-grid-lg-3">\
                        <% _.each(model.get("cols"), function(col, idx) { %>\
                        <div class="checkbox">\
                          <label>\
                            <input type="checkbox" data-colidx="<%= idx %>" <% if (col.show) { %> checked <% } %>>\
                            <%= col.label %>\
                          </label>\
                        </div>\
                        <% }) %>\
                    </div>\
                </div>\
            </div>\
        '),

        events: {
            'change [data-colidx]': function(e) {
                var colidx = $(e.currentTarget).data('colidx');
                this.model.get('cols')[colidx].show = !this.model.get('cols')[colidx].show;
                this.model.trigger('update');
            },
            'change #select-all': function(e) {
                var showAll = $(e.currentTarget).attr('checked') ? false : true;
                _.each(this.model.get('cols'), function(col) {
                    col.show = showAll;
                });
                this.model.trigger('update');
            }
        },

        render: function() {
            this.$el.html(this.template({ model: this.model }));
        }
    })

    var TableDrilldownView = Backbone.View.extend({
        el: '\
            <div>\
                <div class="container" style="width:95%">\
                    <div class="row">\
                        <div class="col-md-12" id="fiscal-totals-container"></div>\
                    </div>\
                    <div class="row">\
                        <div class="col-md-6" id="table-select-container"></div>\
                        <div class="col-md-6" id="column-select-container"></div>\
                    </div>\
                    <div class="row">\
                        <div class="col-md-12" id="table-container"></div>\
                    </div>\
                </div>\
            </div>\
        ',

        initialize: function(options) {
            this.insertTableView();
            this.listenTo(this.model, 'change update', this.insertTableView);
            this.listenTo(this.collection, 'update', this.insertTableView);
            this.resultYears = options.resultYears;
        },

        tableView: null,
        columnSelectView: null,
        tableModel: function() {
            var reference = this.model.reference();
            if (reference) {
                return this.collection.findWhere({ reference: reference });
            }
            return false;
        },
        dataTableOptions: {
            "paging":   false,
            "ordering": false,
            "searching": false,
            "bInfo" : false,
            "dom": 'tB'
        },

        insertTableView: function() {
            if (this.tableView) {
                this.tableView.remove();
            }
            var tableModel = this.tableModel();
            if (tableModel) {
                tableModel.set('row_labels', this.model.rowLabels());
                this.tableView = new TableView({ model: tableModel });
                this.tableView.render();
                this.$el.find('#table-container').html(this.tableView.el);
                this.dataTableOptions.buttons = [
                    {
                        extend: 'print',
                        customize: function ( win ){
                            $(win.document.body).find('h1').html('<center>' + tableModel.get('label').toUpperCase() + ' (' + tableModel.get('year') + ')</center>');
                        }
                    },
                    'copy',
                    'csv',
                    'excel'
                ];
                this.tableView.$el.find('table').dataTable(this.dataTableOptions);
                this.tableView.$el.find("div.dt-buttons.btn-group").addClass('btn-group-justified');
                this.insertColumnSelectView(tableModel);
            }
        },

        insertColumnSelectView: function(tableModel) {
            if (this.columnSelectView) {
                this.columnSelectView.remove();
            }
            this.columnSelectView = new ColumnSelectView({
                model: tableModel,
            });
            this.columnSelectView.render();
            this.$el.find('#column-select-container').html(this.columnSelectView.el);
        },

        render: function() {
            var fiscalTableModel = this.collection.findWhere({ reference: 'fiscal_tots'});
            var fiscalTableView = new TableView({
                model: fiscalTableModel
            });
            fiscalTableView.render();
            this.$el.find('#fiscal-totals-container').html(fiscalTableView.el);
            this.dataTableOptions.buttons = [
                {
                    extend: 'print',
                    customize: function ( win ) {
                        $(win.document.body).find('h1').html('<center>' + fiscalTableModel.get('label').toUpperCase() + '</center>');
                    }
                },
                'copy',
                'csv',
                'excel',
            ];
            fiscalTableView.$el.find('table').dataTable(this.dataTableOptions);
            fiscalTableView.$el.find("div.dt-buttons.btn-group").addClass('btn-group-justified');
            var tableSelectView = new TableSelectView({
                model: this.model,
                resultYears: this.resultYears,
                collection: this.collection
            });
            tableSelectView.render();
            this.$el.find('#table-select-container').html(tableSelectView.el);
        }
    });

    var tablesObj = $('[data-tables]').detach().data('tables');
    var resultYears = tablesObj['result_years'];
    delete tablesObj['result_years'];

    var tables = [];
    _.each(_.keys(tablesObj), function(key) {
        tablesObj[key]['reference'] = key;
        tables.push(tablesObj[key]);
    });

    var tables = new TablesCollection(tables);

    var tableDrilldownView = new TableDrilldownView({
        model: new SelectedTableModel(),
        collection: tables,
        resultYears: resultYears,
    });
    tableDrilldownView.render();
    $('#table-drilldown-container').html(tableDrilldownView.el);
 });
