import pandas as pd
from os import path
import json

#importing Bokeh libraries
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Title
from bokeh.models.widgets import Select, Panel, Tabs
from bokeh.models import HoverTool, WheelZoomTool, ResetTool, SaveTool
from bokeh.models import NumeralTickFormatter
from bokeh.layouts import layout
from bokeh.embed import components
from bokeh.resources import CDN

#import styles
from styles import (PLOT_FORMATS, TITLE_FORMATS, RED, BLUE)


def bubble_plot_tabs(dataframes):
    dataframes = dataframes.copy()

    #remove data from Intellectual Property, Land, and Inventories Categories
    df = pd.DataFrame.from_dict(dataframes['base_output_by_asset'])
    df = df[~df['asset_category'].isin(['Intellectual Property','Land','Inventories'])].copy()
    df = df.where((pd.notnull(df)), 'null')

    #define the size DataFrame
    SIZES = list(range(20, 80, 15))
    df['size'] = pd.qcut(df['assets_c'].values, len(SIZES), labels=SIZES)

    #Form the two Categories: Equipment and Structures
    equipment_df = df[(~df.asset_category.str.contains('Structures')) & (~df.asset_category.str.contains('Buildings'))]
    structure_df = df[(df.asset_category.str.contains('Structures')) | (df.asset_category.str.contains('Buildings'))]

    #Choose the year
    data_sources = {}
    format_fields = ['mettr_c']

    # Make short category
    make_short = {'Instruments and Communications Equipment': 'Instruments and Communications',
                  'Office and Residential Equipment': 'Office and Residential',
                  'Other Equipment': 'Other',
                  'Transportation Equipment': 'Transportation',
                  'Other Industrial Equipment': 'Other Industrial',
                  'Nonresidential Buildings': 'Nonresidential Bldgs',
                  'Residential Buildings': 'Residential Bldgs',
                  'Mining and Drilling Structures': 'Mining and Drilling',
                  'Other Structures': 'Other'}

    equipment_df['short_category'] = equipment_df['asset_category'].map(make_short)
    structure_df['short_category'] = structure_df['asset_category'].map(make_short)

    #Add the Reform and the Baseline to Equipment Asset
    for f in format_fields:
        equipment_copy = equipment_df.copy()
        equipment_copy['reform'] = equipment_copy[f]
        equipment_copy['baseline'] = equipment_copy['mettr_c']
        equipment_copy['hover'] = equipment_copy.apply(lambda x: "{0:.1f}%".format(x[f] * 100), axis=1)
        #equipment_copy['hover2016'] = equipment_copy.apply(lambda x: "{0:.1f}%".format(x['mettr_c_2016'] * 100), axis=1)
        data_sources['equipment_' + f] = ColumnDataSource(equipment_copy)

    fudge_factor = '                          ' # this a spacer for the y-axis label

    #Add the Reform and the Baseline to Structures Asset
    for f in format_fields:
        structure_copy = structure_df.copy()
        structure_copy['reform'] = structure_copy[f]
        structure_copy['baseline'] = structure_copy['mettr_c']
        structure_copy['hover'] = structure_copy.apply(lambda x: "{0:.1f}%".format(x[f] * 100), axis=1)
        structure_copy['short_category'] = structure_copy['short_category'].str.replace('Residential Bldgs', fudge_factor + 'Residential Bldgs')
        data_sources['structure_' + f] = ColumnDataSource(structure_copy)

    #Define categories for Equipments assets
    equipment_assets = ['Computers and Software',
                        'Instruments and Communications',
                        'Office and Residential',
                        'Transportation',
                        'Industrial Machinery',
                        'Other Industrial',
                        'Other']

    #Define categories for Structures assets
    structure_assets = ['Residential Bldgs',
                        'Nonresidential Bldgs',
                        'Mining and Drilling',
                        'Other']

    # Equipment plot
    p = figure(plot_height=540,
               plot_width=990,
               x_range = (-.05, .51),
               y_range=list(reversed(equipment_assets)),
               tools='hover',
               background_fill_alpha=0,
               **PLOT_FORMATS)
    p.add_layout(Title(text='Marginal Effective Tax Rates on Corporate Investments in Equipment', **TITLE_FORMATS),"above")

    hover = p.select(dict(type=HoverTool))
    hover.tooltips = [('Asset', ' @Asset (@hover)')]

    source=data_sources['equipment_mettr_c'];

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

    p.circle(x='baseline',
             y='short_category',
             color="#AAAAAA",
             size='size',
             line_color="#333333",
             line_alpha=.1,
             fill_alpha=0,
             source=ColumnDataSource(data_sources['equipment_mettr_c'].data),
             alpha=.4)

    equipment_renderer = p.circle(x='reform',
                                  y='short_category',
                                  size='size',
                                  #line_color="white",
                                  source=data_sources['equipment_mettr_c'],
                                  color = BLUE,
                                  alpha=.4,
                                  line_color = "firebrick",
                                  line_dash = [8, 3],
                                  line_width = 1)
    # Style the tools
    p.add_tools(WheelZoomTool(), ResetTool(), SaveTool())
    p.toolbar_location = "right"
    p.toolbar.logo = None

    # Structures plot
    p2 = figure(plot_height=540,
                plot_width=990,
                x_range = (-.05, .51),
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


    p2.circle(x='baseline',
              y='short_category',
              color=RED,
              size='size',
              line_color="#333333",
              line_alpha=.1,
              fill_alpha=0,
              source=ColumnDataSource(data_sources['structure_mettr_c'].data),
              alpha=.4)

    p2.outline_line_width = 1
    p2.outline_line_alpha = 1
    p2.outline_line_color = "black"

    structure_renderer = p2.circle(x='reform',
                                   y='short_category',
                                   color=BLUE,
                                   size='size',
                                   source=data_sources['structure_mettr_c'],
                                   alpha=.4,
                                   line_color="firebrick",
                                   line_dash=[8, 3],
                                   line_width=1)

    # Style the tools
    p2.add_tools(WheelZoomTool(), ResetTool(), SaveTool())
    p2.toolbar_location = "right"
    p2.toolbar.logo = None

    # Create Tabs
    tab = Panel(child=p, title='Equipment')
    tab2 = Panel(child=p2, title='Structures')
    tabs = Tabs(tabs=[tab, tab2])

    js, div = components(tabs)
    cdn_js = CDN.js_files[0]
    cdn_css = CDN.css_files[0]

    return js, div, cdn_js, cdn_css
