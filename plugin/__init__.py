"""KiCad toolbar button: save the board and send it to SolidCraft."""

import os
import shutil
import subprocess

import pcbnew
import wx

HERE = os.path.dirname(os.path.realpath(__file__))


class PushToSolidCraft(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Push to SolidCraft"
        self.category = "3D"
        self.description = "Save the board and open it in SolidCraft as a new design"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(HERE, "icon.png")

    def Run(self):
        board = pcbnew.GetBoard()
        path = board.GetFileName()
        if not path:
            wx.MessageBox("Save the board once first, so it has a file name.",
                          "Push to SolidCraft")
            return
        pcbnew.SaveBoard(path, board)
        python = shutil.which("python3") or shutil.which("python") or "python3"
        subprocess.Popen([python, "-I", os.path.join(HERE, "push.py"), path],
                         start_new_session=True, cwd=os.path.dirname(path),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


PushToSolidCraft().register()
