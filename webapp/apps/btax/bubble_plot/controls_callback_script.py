CONTROLS_CALLBACK_SCRIPT = """
var equip_data = equip_source.data;
var struc_data = struc_source.data;

var c_nc_button = c_nc_buttons.active;
var format_button = format_buttons.active;
var type_button = type_buttons.active;
var interest_button = interest_buttons.active;

if (c_nc_button == 0) {
    var c_nc_str = '_c';
} else if (c_nc_button == 1) {
    var c_nc_str = '_nc';
}

if (format_button == 0) {
    var format_str = 'base_';
} else if (format_button == 1) {
    var format_str = 'reform_';
} else if (format_button == 2) {
    var format_str = 'change_';
}

if (type_button == 0) {
    var type_str = ''
} else if (type_button == 1) {
    var type_str = '_e'
} else if (type_button == 2) {
    var type_str = '_d'
}

if (interest_button == 0) {
    interest_str = '_mettr';
} else if (interest_button == 1) {
    interest_str = '_metr';
} else if (interest_button == 2) {
    interest_str = '_rho';
} else if (interest_button == 3) {
    interest_str = '_z';
}

var new_equip_data = eval(format_str + 'equipment' + interest_str + c_nc_str + type_str).data
var new_struc_data = eval(format_str + 'structure' + interest_str + c_nc_str + type_str).data

debugger

for (var i = 0; i < equip_data['size_c'].length; i++) {
    equip_data['size'][i] = new_equip_data['size' + c_nc_str][i];
    struc_data['size'][i] = new_struc_data['size' + c_nc_str][i];

    equip_data['rate'][i] = new_equip_data['rate'][i];
    struc_data['rate'][i] = new_struc_data['rate'][i];
}

equip_source.trigger('change');
struc_source.trigger('change');
"""
