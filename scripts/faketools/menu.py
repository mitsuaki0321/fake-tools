"""
Add a menu to the maya main window.
"""

import os
from logging import getLogger

import maya.cmds as cmds
import maya.mel as mel

from .tools import singleCommand_menu

MENU_NAME = 'FakeTools'

tools = [{'label': 'Remote Slider', 'module': 'remote_slider_ui'},
         {'label': 'Scene Optimizer', 'module': 'scene_optimizer_ui'},
         {'label': 'Selecter', 'module': 'selecter_ui'},
         {'label': 'Transform Connector', 'module': 'transform_connector_ui'},
         {'label': 'Transform Creator', 'module': 'transform_creator_ui'},
         {'label': 'Transform on Curve Creator', 'module': 'transform_creator_on_curve_ui'},
         {'label': 'Membership Handler', 'module': 'membership_handler_ui'},
         {'label': 'SkinWeights Import/Export', 'module': 'skinWeights_import_export_ui'},
         {'label': 'SkinWeights Tools', 'module': 'skinWeights_tools_ui'},
         {'label': 'SkinWeights Relax', 'module': 'skinWeights_relax_ui'},
         {'label': 'SkinWeights CopyPaste', 'module': 'skinWeights_copy_paste_ui'},
         {'label': 'CurveSurface Creator', 'module': 'curveSurface_creator_ui'},
         {'label': 'DrivenKey Tools', 'module': 'drivenkey_tools_ui'},
         {'label': 'Component Selecter', 'module': 'component_selecter_ui'},
         {'label': 'Attribute Lister', 'module': 'attribute_lister_ui'},
         {'label': 'Connection Lister', 'module': 'connection_lister_ui'},
         {'label': 'Node Stocker', 'module': 'node_stocker_ui'},
         {'label': 'Retarget Transform', 'module': 'retarget_transform_ui'},
         {'label': 'Retarget Mesh', 'module': 'retarget_mesh_ui'},
         {'label': 'BoundingBox Creator', 'module': 'boundingbox_creator_ui'},
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
