"""
Maya-specific functions in UI.
"""

import traceback

import maya.cmds as cmds
import maya.mel as mel
from maya.api.OpenMaya import MGlobal


class Undo:
    """Context manager for undo chunk.
    """
    open_chunk = True

    def __init__(self, operation_name='operation'):
        self.name = operation_name
        self.close_chunk = False

    def __enter__(self):
        if Undo.open_chunk:
            self.close_chunk = True
            Undo.open_chunk = False
            cmds.undoInfo(openChunk=True, chunkName=self.name)

        return self

    def __exit__(self, typ, value, trace):
        if self.close_chunk:
            cmds.undoInfo(closeChunk=True)
            Undo.open_chunk = True


def undo_chunk(chunk_name):
    """Decorator for undo chunk.

    Args:
        chunk_name (str): Name of the undo chunk.

    Returns:
        function: Decorated function.
    """
    def deco(func):
        def wrap(*args, **kwargs):
            with Undo(chunk_name):
                return func(*args, **kwargs)

        return wrap

    return deco


def without_undo(func):
    """Decorator for without undo.

    Args:
        func (function): Function to decorate.

    Returns:
        function: Decorated function.
    """
    def wrap(*args, **kwargs):
        cmds.undoInfo(stateWithoutFlush=False)
        try:
            return func(*args, **kwargs)
        finally:
            cmds.undoInfo(stateWithoutFlush=True)

    return wrap


def error_handler(func):
    """Error handler.

    Args:
        func (function): Function to decorate.

    Returns:
        function: Decorated function.
    """
    def wrap(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            traceback.print_exc()
            MGlobal.displayError(str(e))

    return wrap


def selection_handler(func):
    """Selection handler for selecter tools.

    Args:
        func (function): Function to decorate.

    Returns:
        function: Decorated function.
    """
    def wrap(*args, **kwargs):
        sel_nodes = cmds.ls(sl=True)
        result_nodes = func(*args, **kwargs)

        mod_keys = get_modifiers()
        if not mod_keys:
            cmds.select(result_nodes, r=True)
        elif ['Shift', 'Ctrl'] == mod_keys:
            cmds.select(sel_nodes, r=True)
            cmds.select(result_nodes, add=True)
        elif 'Shift' in mod_keys:
            cmds.select(sel_nodes, r=True)
            cmds.select(result_nodes, tgl=True)
        elif 'Ctrl' in mod_keys:
            cmds.select(sel_nodes, r=True)
            cmds.select(result_nodes, d=True)

    return wrap


def get_channels(long_name=True) -> list[str]:
    """Get attribute names from the channel box.

    Returns:
        list[str]: Attribute names.
    """
    g_channel_box = mel.eval("$temp=$gChannelBoxName")
    channels = cmds.channelBox(g_channel_box, q=True, sma=True)

    if not channels:
        return []

    if not long_name:
        return channels
    else:
        sel_nodes = cmds.ls(sl=True)
        return [cmds.attributeQuery(ch, n=sel_nodes[-1], ln=True) for ch in channels]


def get_modifiers() -> list[str]:
    """Get the current modifier keys.

    Returns:
        list[str]: Modifier keys.
    """
    mods = cmds.getModifiers()
    keys = []
    if (mods & 1) > 0:
        keys.append('Shift')
    if (mods & 4) > 0:
        keys.append('Ctrl')
    if (mods & 8) > 0:
        keys.append('Alt')
    if (mods & 16):
        keys.append('Command/Windows')

    return keys


class progress_bar(object):

    def __init__(self, maxVal, **kwargs):
        msg = kwargs.get('message', kwargs.get('msg', 'Calculation ...'))
        self.pBar = mel.eval('$tmp = $gMainProgressBar')
        cmds.progressBar(self.pBar, e=True, beginProgress=True, isInterruptable=True, status=msg, maxValue=maxVal)

    def breakPoint(self):
        if cmds.progressBar(self.pBar, q=True, isCancelled=True):
            return True
        else:
            cmds.progressBar(self.pBar, e=True, step=1)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        cmds.progressBar(self.pBar, e=True, endProgress=True)
