CONTROLS_CALLBACK_SCRIPT = """
var equip_data = equip_source.data;
var struc_data = struc_source.data;

var c_nc_button = c_nc_buttons.active;
var format_button = format_buttons.active;
var type_button = type_buttons.active;
var interest_button = interest_buttons.active;

var n_nc_str, format_str, type_str, interest_button

if (c_nc_button == 0) {
    c_nc_str = '_c';
} else if (c_nc_button == 1) {
    c_nc_str = '_nc';
}

if (format_button == 0) {
    format_str = 'base_';
} else if (format_button == 1) {
    format_str = 'reform_';
} else if (format_button == 2) {
    format_str = 'change_';
}

if (type_button == 0) {
    type_str = ''
} else if (type_button == 1) {
    type_str = '_e'
} else if (type_button == 2) {
    type_str = '_d'
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

equip_data['size'] = []
equip_data['rate'] = []
equip_data['hover'] = []
equip_data['short_category'] = []
for (var i = 0; i < new_equip_data['size'].length; i++) {
    equip_data['size'].push(new_equip_data['size' + c_nc_str][i]);
    equip_data['rate'].push(new_equip_data['rate'][i]);
    equip_data['hover'].push(new_equip_data['hover'][i]);
    equip_data['short_category'].push(new_equip_data['short_category'][i]);
}

struc_data['size'] = []
struc_data['rate'] = []
struc_data['hover'] = []
struc_data['short_category'] = []
for (var i = 0; i < new_struc_data['size'].length; i++) {
    struc_data['size'].push(new_struc_data['size' + c_nc_str][i]);
    struc_data['rate'].push(new_struc_data['rate'][i]);
    struc_data['hover'].push(new_struc_data['hover'][i]);
    struc_data['short_category'].push(new_struc_data['short_category'][i]);
}

equip_source.change.emit();
struc_source.change.emit();
"""
