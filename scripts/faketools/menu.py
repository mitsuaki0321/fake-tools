"""
Add a menu to the maya main window.
"""

import os
from logging import getLogger

import maya.cmds as cmds
import maya.mel as mel

from .tools import singleCommand_menu

MENU_NAME = 'FakeTools'

tools = [{'label': 'Remote Slider', 'module': 'remote_slider'},
         {'label': 'Scene Optimizer', 'module': 'scene_optimizer'},
         {'label': 'Selecter', 'module': 'selecter'},
         {'label': 'Transform Connecter', 'module': 'transform_connecter'},
         {'label': 'Transform Creater', 'module': 'transform_creater'},
         {'label': 'Transform on Curve Creater', 'module': 'transform_creater_on_curve'},
         {'label': 'Membership Handler', 'module': 'membership_handler'},
         {'label': 'SkinWeights Import/Export', 'module': 'skinWeights_import_export'},
         {'label': 'SkinWeights Tools', 'module': 'skinWeights_tools'},
         {'label': 'SkinWeights CopyPaste', 'module': 'skinWeights_copy_paste'},
         {'label': 'CurveSurface Creator', 'module': 'curveSurface_creator'},
         {'label': 'DrivenKey Tools', 'module': 'drivenkey_tools'},
         {'label': 'Component Selecter', 'module': 'component_selecter'},
         {'label': 'Attribute Lister', 'module': 'attribute_lister'},
         {'label': 'Connection Lister', 'module': 'connection_lister'},
         {'label': 'Node Stocker', 'module': 'node_stocker'},
         {'label': 'Position Import/Export', 'module': 'position_import_export'},
         ]


logger = getLogger(__name__)


def add_menu():
    """Add a menu to the maya main window.
    """
    main_window = mel.eval('$tmpVar=$gMainWindow')
    menu = '{}_{}'.format('_'.join(__name__.split('.')), MENU_NAME)

    if cmds.menu(menu, exists=True):
        logger.debug(f'Delete menu: {menu}')
        cmds.deleteUI(menu)

    menu = cmds.menu(menu, label=MENU_NAME, parent=main_window, tearOff=True)

    # Add single commands to the menu
    singleCommand_menu.show_menu(parent_menu=menu)

    logger.debug(f'Add single command menu: {menu}')

    # Add tools to the menu
    cmds.menuItem(divider=True, parent=menu)

    for tool in tools:
        cmd = f"import faketools.tools.{tool['module']}; faketools.tools.{tool['module']}.show_ui()"
        cmds.menuItem(label=tool['label'], command=cmd, parent=menu)

    logger.debug(f'Add main menu: {menu}')

    # Add help menu
    cmds.menuItem(divider=True, parent=menu)

    idx_html = os.path.join(os.path.dirname(__file__), 'docs', 'index.html').replace('\\', '/')
    url = 'file://{}'.format(idx_html)
    cmds.menuItem(label='Help', command='import webbrowser; webbrowser.open("{}")'.format(url), parent=menu)

    logger.debug(f'Add help menu: {menu}')
