"""Single Command Menus."""

from logging import getLogger

import maya.cmds as cmds
import maya.mel as mel

from ..command import singleCommands
from ..lib.lib_singleCommand import AllCommand, PairCommand, SceneCommand

logger = getLogger(__name__)

MENU_NAME = "Single Commands"


def show_menu(parent_menu: str | None = None) -> None:
    """Show the menu.

    Notes:
        - If a parent menu is specified, it will be added to that menu.
        - If no parent menu is specified, it will be added to the main window.

    Args:
        parent_menu (str, optional): The parent menu to add the menu to. Defaults to None.
    """
    if parent_menu:
        if not cmds.menu(parent_menu, exists=True):
            cmds.error(f"Parent menu does not exist: {parent_menu}")

        menu = cmds.menuItem(label=MENU_NAME, subMenu=True, parent=parent_menu, tearOff=True)
    else:
        parent_window = mel.eval("$tmpVar=$gMainWindow")
        menu = "{}_{}".format("_".join(__name__.split(".")), MENU_NAME)
        if cmds.menu(menu, exists=True):
            cmds.deleteUI(menu)

        menu = cmds.menu(menu, label=MENU_NAME, parent=parent_window, tearOff=True)

    # Add single commands to the menu
    # Scene commands
    scene_commands = singleCommands.SCENE_COMMANDS
    if scene_commands:
        for cls_name in scene_commands:
            cmd = f"import {__name__}; {__name__}.execute_single_commands('{cls_name}')"
            cmds.menuItem(label=cls_name, command=cmd, parent=menu)

        cmds.menuItem(divider=True, parent=menu)

    # Add all commands
    all_commands = singleCommands.ALL_COMMANDS
    if all_commands:
        for cls_name in all_commands:
            cmd = f"import {__name__}; {__name__}.execute_single_commands('{cls_name}')"
            cmds.menuItem(label=cls_name, command=cmd, parent=menu)

        cmds.menuItem(divider=True, parent=menu)

    # Add pair commands
    pair_commands = singleCommands.PAIR_COMMANDS
    if pair_commands:
        for cls_name in pair_commands:
            cmd = f"import {__name__}; {__name__}.execute_single_commands('{cls_name}')"
            cmds.menuItem(label=cls_name, command=cmd, parent=menu)

    logger.debug(f"Add single command menu: {menu}")


def execute_single_commands(single_command_name: str) -> None:
    """Execute the single command.

    Args:
        command_name (str): The single command class name.
    """
    if not hasattr(singleCommands, single_command_name):
        cmds.error(f"Command does not exist: {single_command_name}")

    single_command_cls = getattr(singleCommands, single_command_name)
    if issubclass(single_command_cls, SceneCommand):
        single_command_cls()
    else:
        sel_nodes = cmds.ls(sl=True, type="transform")
        if not sel_nodes:
            cmds.error("No transform nodes selected")

        if issubclass(single_command_cls, AllCommand):
            single_command_cls(sel_nodes)
        elif issubclass(single_command_cls, PairCommand):
            if len(sel_nodes) < 2:
                cmds.error("Please select at least 2 nodes")

            single_command_cls([sel_nodes[0]], sel_nodes[1:])
