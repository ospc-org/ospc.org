import pandas as pd
from os import path
import json
pd.options.mode.chained_assignment = None

# importing Bokeh libraries
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Title, CustomJS
from bokeh.models.widgets import Select, Panel, Tabs, RadioButtonGroup
from bokeh.models import HoverTool, WheelZoomTool, ResetTool, SaveTool
from bokeh.models import NumeralTickFormatter
from bokeh.layouts import gridplot
from bokeh.embed import components
from bokeh.resources import CDN

# import styles and callback
from styles import (PLOT_FORMATS, TITLE_FORMATS, RED, BLUE)
from controls_callback_script import CONTROLS_CALLBACK_SCRIPT


def bubble_plot_tabs(dataframes):
    dataframes = dataframes.copy()

    # remove data from Intellectual Property, Land, and Inventories Categories
    base_df = pd.DataFrame.from_dict(dataframes['base_output_by_asset'])
    reform_df = pd.DataFrame.from_dict(dataframes['reform_output_by_asset'])
    change_df = pd.DataFrame.from_dict(dataframes['changed_output_by_asset'])

    list_df = [base_df, reform_df, change_df]
    list_string = ['base', 'reform', 'change']

    data_sources = {}
    for i, df in enumerate(list_df):
        df = df[~df['asset_category'].isin(['Intellectual Property','Land','Inventories'])].copy()
        df = df.where((pd.notnull(df)), 'null')

        # define the size DataFrame
        if sum(df['assets_c']) == 0:
            df['size'] = df['assets_c']
            df['size_c'] = df['assets_c']
            df['size_nc'] = df['assets_nc']
        else:
            SIZES = list(range(20, 80, 15))
            df['size'] = pd.qcut(df['assets_c'].values, len(SIZES), labels=SIZES)
            df['size_c'] = pd.qcut(df['assets_c'].values, len(SIZES), labels=SIZES)
            df['size_nc'] = pd.qcut(df['assets_nc'].values, len(SIZES), labels=SIZES)

        # Form the two Categories: Equipment and Structures
        equipment_df = df[(~df.asset_category.str.contains('Structures')) & (~df.asset_category.str.contains('Buildings'))]
        structure_df = df[(df.asset_category.str.contains('Structures')) | (df.asset_category.str.contains('Buildings'))]

        format_fields = ['metr_c', 'metr_nc', 'metr_c_d', 'metr_nc_d', 'metr_c_e', 'metr_nc_e',
                         'mettr_c', 'mettr_nc', 'mettr_c_d', 'mettr_nc_d', 'mettr_c_e', 'mettr_nc_e',
                         'rho_c', 'rho_nc', 'rho_c_d', 'rho_nc_d', 'rho_c_e', 'rho_nc_e',
                         'z_c', 'z_nc', 'z_c_d', 'z_nc_d', 'z_c_e', 'z_nc_e']

        # Make short category
        make_short = {'Instruments and Communications Equipment': 'Instruments and Communications',
                      'Office and Residential Equipment': 'Office and Residential',
                      'Other Equipment': 'Other',
                      'Transportation Equipment': 'Transportation',
                      'Other Industrial Equipment': 'Other Industrial',
                      'Nonresidential Buildings': 'Nonresidential Bldgs',
                      'Residential Buildings': 'Residential Bldgs',
                      'Mining and Drilling Structures': 'Mining and Drilling',
                      'Other Structures': 'Other',
                      'Computers and Software': 'Computers and Software',
                      'Industrial Machinery': 'Industrial Machinery'}

        equipment_df['short_category'] = equipment_df['asset_category'].map(make_short)
        structure_df['short_category'] = structure_df['asset_category'].map(make_short)

        # Add the Reform and the Baseline to Equipment Asset
        for f in format_fields:
            equipment_copy = equipment_df.copy()
            equipment_copy['rate'] = equipment_copy[f]
            equipment_copy['hover'] = equipment_copy.apply(lambda x: "{0:.1f}%".format(x[f] * 100), axis=1)
            data_sources[list_string[i] + '_equipment_' + f] = ColumnDataSource(equipment_copy)

        fudge_factor = '                          ' # this a spacer for the y-axis label

        # Add the Reform and the Baseline to Structures Asset
        for f in format_fields:
            structure_copy = structure_df.copy()
            structure_copy['rate'] = structure_copy[f]
            structure_copy['hover'] = structure_copy.apply(lambda x: "{0:.1f}%".format(x[f] * 100), axis=1)
            structure_copy['short_category'] = structure_copy['short_category'].str.replace('Residential Bldgs', fudge_factor + 'Residential Bldgs')
            data_sources[list_string[i] + '_structure_' + f] = ColumnDataSource(structure_copy)

    # Create initial datasets to plot with
    equip_source = data_sources['base_equipment_mettr_c']
    struc_source = data_sources['base_structure_mettr_c']

    # Define categories for Equipments assets
    equipment_assets = ['Computers and Software',
                        'Instruments and Communications',
                        'Office and Residential',
                        'Transportation',
                        'Industrial Machinery',
                        'Other Industrial',
                        'Other']

    # Define categories for Structures assets
    structure_assets = ['Residential Bldgs',
                        'Nonresidential Bldgs',
                        'Mining and Drilling',
                        'Other']

    # Equipment plot
    p = figure(plot_height=540,
               plot_width=990,
               y_range=list(reversed(equipment_assets)),
               tools='hover',
               background_fill_alpha=0,
               **PLOT_FORMATS)
    p.add_layout(Title(text='Marginal Effective Tax Rates on Corporate Investments in Equipment', **TITLE_FORMATS), "above")

    hover = p.select(dict(type=HoverTool))
    hover.tooltips = [('Asset', ' @Asset (@hover)')]

    p.xaxis.axis_label = "Marginal Effective Tax Rate"
    p.xaxis[0].formatter = NumeralTickFormatter(format="0.1%")

    p.toolbar_location = None
    p.min_border_right = 5

    p.outline_line_width = 5
    p.border_fill_alpha = 0
    p.xaxis.major_tick_line_color = "firebrick"
    p.xaxis.major_tick_line_width = 3
    p.xaxis.minor_tick_line_color = "orange"

    p.outline_line_width = 1
    p.outline_line_alpha = 1
    p.outline_line_color = "black"

    p.circle(x='rate',
             y='short_category',
             color=BLUE,
             size='size',
             line_color="#333333",
             fill_alpha=.4,
             source=equip_source,
             alpha=.4)

    # Style the tools
    p.add_tools(WheelZoomTool(), ResetTool(), SaveTool())
    p.toolbar_location = "right"
    p.toolbar.logo = None

    # Structures plot
    p2 = figure(plot_height=540,
                plot_width=990,
                y_range=list(reversed(structure_assets)),
                tools='hover',
                background_fill_alpha=0,
                **PLOT_FORMATS)
    p2.add_layout(Title(text='Marginal Effective Tax Rates on Corporate Investments in Structures', **TITLE_FORMATS),"above")

    hover = p2.select(dict(type=HoverTool))
    hover.tooltips = [('Asset', ' @Asset (@hover)')]
    p2.xaxis.axis_label = "Marginal Effective Tax Rate"
    p2.xaxis[0].formatter = NumeralTickFormatter(format="0.1%")
    p2.toolbar_location = None
    p2.min_border_right = 5
    p2.outline_line_width = 0
    p2.border_fill_alpha = 0

    p2.xaxis.major_tick_line_color = "firebrick"
    p2.xaxis.major_tick_line_width = 3
    p2.xaxis.minor_tick_line_color = "orange"

    p2.circle(x='rate',
              y='short_category',
              color=RED,
              size='size',
              line_color="#333333",
              # line_alpha=.1,
              fill_alpha=.4,
              source=struc_source,
              alpha=.4)

    p2.outline_line_width = 1
    p2.outline_line_alpha = 1
    p2.outline_line_color = "black"

    # Style the tools
    p2.add_tools(WheelZoomTool(), ResetTool(), SaveTool())
    p2.toolbar_location = "right"
    p2.toolbar.logo = None


    data_sources['equip_source'] = equip_source
    data_sources['struc_source'] = struc_source
    controls_callback = CustomJS(args=data_sources,
                                 code=CONTROLS_CALLBACK_SCRIPT)

    c_nc_buttons = RadioButtonGroup(labels=['Corporate', 'Noncorporate'],
                                    active=0, callback=controls_callback)
    controls_callback.args['c_nc_buttons'] = c_nc_buttons

    format_buttons = RadioButtonGroup(labels=['Baseline', 'Reform', 'Change'],
                                      active=0, callback=controls_callback)
    controls_callback.args['format_buttons'] = format_buttons

    interest_buttons = RadioButtonGroup(labels=['METTR', 'METR', 'Cost of Capital', 'Depreciation'],
                                        active=0, width=700, callback=controls_callback)
    controls_callback.args['interest_buttons'] = interest_buttons

    type_buttons = RadioButtonGroup(labels=['Typically Financed', 'Equity Financed', 'Debt Financed'],
                                    active=0, width=700, callback=controls_callback)
    controls_callback.args['type_buttons'] = type_buttons

    # Create Tabs
    tab = Panel(child=p, title='Equipment')
    tab2 = Panel(child=p2, title='Structures')
    tabs = Tabs(tabs=[tab, tab2])
    layout = gridplot(
        children=[[tabs],
                  [c_nc_buttons, interest_buttons],
                  [format_buttons, type_buttons]],
    )

    js, div = components(layout)
    cdn_js = CDN.js_files[0]
    cdn_css = CDN.css_files[0]

    return js, div, cdn_js, cdn_css
