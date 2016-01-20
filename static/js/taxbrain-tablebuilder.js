'use strict';

var TableModel = Backbone.Model.extend();

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
        console.log(table);
        return table;
    }
});

var TablesCollection = Backbone.Collection.extend({
    model: TableModel
});

var TableView = Backbone.View.extend({
    template: _.template('\
        <div class="panel panel-default">\
            <div class="panel-heading">\
                <div class="panel-title"><strong><%= model.get("label") %></strong></div>\
            </div>\
            <div class="panel-body" style="overflow: scroll">\
                <table class="table">\
                    <thead>\
                        <tr>\
                            <% _.each(model.get("col_labels"), function(col_label) { %>\
                                <th><%= col_label %></th>\
                            <% }) %>\
                        </tr>\
                    </thead>\
                    <tbody>\
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
    el: '<div class="panel panel-default">\
          <div class="panel-heading">\
            <h3 class="panel-title">Table Drilldown</h3>\
          </div>\
          <div class="panel-body">\
            <ul class="nav nav-pills nav-justified">\
              <li class="active" data-difference="false"><a href="#">Diagnostic</a></li>\
              <li data-difference="true"><a href="#">Difference</a></li>\
            </ul>\
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
            <ul class="nav nav-pills nav-justified">\
              <li class="active" data-income="expanded"><a href="#">Expanded Income</a></li>\
              <li class="disabled" data-income="adjusted"><a href="#" disabled>Adjusted Income</a></li>\
            </ul>\
            <br>\
            <ul class="nav nav-pills nav-justified">\
              <li class="active" data-grouping="bin"><a href="#">Income Bins</a></li>\
              <li data-grouping="dec"><a href="#">Income Decimals</a></li>\
            </ul>\
          </div>\
        </div>',

    events: {
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

});

var ColumnSelectView = Backbone.View.extend({
    template: _.template('\
        <div class="panel panel-default">\
            <div class="panel-heading">\
                <h3 class="panel-title">Select Columns</h3>\
            </div>\
            <div class="panel-body">\
                <div class="block-grid-md-3 block-grid-sm-3 block-grid-lg-3">\
                    <% _.each(model.get("col_labels"), function(label) { %>\
                    <div class="checkbox">\
                      <label>\
                        <input type="checkbox" value="">\
                        <%= label %>\
                      </label>\
                    </div>\
                    <% }) %>\
                </div>\
            </div>\
        </div>\
    '),

    render: function() {
        this.$el.html(this.template({ model: this.model }));
    }
})

var TableDrilldownView = Backbone.View.extend({
    el: '\
        <div>\
            <div class="container" style="width:95%">\
                <div class="row">\
                    <div class="col-md-6 col-md-offset-3" id="table-select-container"></div>\
                </div>\
                <div class="row">\
                    <div class="col-md-12" id="column-select-container"></div>\
                </div>\
                <div class="row">\
                    <div class="col-md-12" id="table-container"></div>\
                </div>\
            </div>\
        </div>\
    ',

    initialize: function() {
        this.insertTableView();
        this.listenTo(this.model, 'change', this.insertTableView);
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

    insertTableView: function() {
        if (this.tableView) {
            this.tableView.remove();
        }
        var tableModel = this.tableModel();
        if (tableModel) {
            this.tableView = new TableView({ model: tableModel });
            this.tableView.render();
            this.$el.find('#table-container').html(this.tableView.el);
            this.insertColumnSelectView(tableModel);
        }
    },

    insertColumnSelectView: function(tableModel) {
        if (this.columnSelectView) {
            this.columnSelectView.remove();
        }
        this.columnSelectView = new ColumnSelectView({ model: tableModel });
        this.columnSelectView.render();
        this.$el.find('#column-select-container').html(this.columnSelectView.el);
    },

    render: function() {
        var tableSelectView = new TableSelectView({ model: this.model });
        this.$el.find('#table-select-container').html(tableSelectView.el);
    }
});

var tablesObj = $('[data-tables]').detach().data('tables');
var resultYears = tablesObj['result_years'];

var tables = [];
_.each(_.keys(tablesObj), function(key) {
    if (key !== 'result_years') {
        tablesObj[key]['reference'] = key;
        tables.push(tablesObj[key]);
    }
});

var tables = new TablesCollection(tables);
var tableDrilldownView = new TableDrilldownView({ model: new SelectedTableModel(), collection: tables });
tableDrilldownView.render();
$('#table-drilldown-container').html(tableDrilldownView.el);