#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Christian Relling (jcrelling@gmail.com)"
__version__ = "1.1"
__date__ = "10 Oct 2011"
__name_app__ = "xPhotOrganizer"

import sys
import os
import re
import pyexiv2
import shutil
from PyQt4 import QtGui, QtCore
from util import get_config, write_config, count_files

class MainWindows(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindows, self).__init__()
        self.initUI()
                
    def initUI(self):
        self.setGeometry(200, 200, 600, 550)
        self.setWindowTitle(__name_app__)
        
        self.config = get_config()
        
        try:
            sys.argv[1]
        except IndexError:
            self.root_path = self.config.get('main', 'source_dir')
        else:
            self.root_path = sys.argv[1]
        
        try:
            sys.argv[2]
        except IndexError:
            self.dest_path = self.config.get('main', 'dest_dir')
        else:
            self.dest_path = sys.argv[2]
            
        self.DirList = []
        self.TotalQty = 0
            
        self.treeDir = treeDir(self, self.root_path)
        
        self.chkSubDir = QtGui.QCheckBox("SubDirectories?", self)
        self.chkSubDir.setGeometry(QtCore.QRect(10, 420, 151, 31))
        self.chkSubDir.setCheckState(2)
        
        self.lstSelectedDir = QtGui.QListWidget(self)
        self.lstSelectedDir.setGeometry(QtCore.QRect(320, 50, 256, 361))
                
        self.pushButtonRight = QtGui.QPushButton("->", self)
        self.pushButtonRight.setGeometry(QtCore.QRect(280, 70, 31, 27))
        self.pushButtonRight.clicked.connect(self.pushButtonRightClk)
        
        self.pushButtonLeft = QtGui.QPushButton("<-", self)
        self.pushButtonLeft.setGeometry(QtCore.QRect(280, 100, 31, 27))
        self.pushButtonLeft.clicked.connect(self.pushButtonLeftClk)
        
        self.pushButtonClr = QtGui.QPushButton("Clr", self)
        self.pushButtonClr.setGeometry(QtCore.QRect(280, 140, 31, 27))
        self.pushButtonClr.clicked.connect(self.pushButtonClrClk)
                
        self.DstFolder = QtGui.QLabel("Destination folder: "+self.dest_path, self)
        self.DstFolder.setGeometry(QtCore.QRect(10, 480, 500, 31))
        
        self.sb = QtGui.QStatusBar(self)
        self.setStatusBar(self.sb)
        self.pb = QtGui.QProgressBar(self.sb)
        self.sb.addPermanentWidget(self.pb)
        self.pb.hide()
        
        self.tb = QtGui.QToolBar(self)
        self.tb.setToolButtonStyle(2)
        self.tb.addAction(QtGui.QIcon("image/source1.png"), 'Source folder', self.ChgDirBtnClk)
        self.tb.addAction(QtGui.QIcon("image/destination1.png"), 'Destination folder', self.ChgDstDirBtnClk)
        self.tb.addSeparator()
        self.tb.addAction(QtGui.QIcon("image/run1.png"), 'Copy files', self.CpyFileBtnClk)
        self.tb.addSeparator()
        self.tb.addAction(QtGui.QIcon("image/config1.png"), 'Config', self.ConfigurationW)
        self.tb.addSeparator()
        self.tb.addAction(QtGui.QIcon("image/exit1.png"), 'Exit', self.destroy)
        self.tb.adjustSize()
        
        self.mi_thread = WorkThread()
        QtCore.QObject.connect(self.mi_thread, QtCore.SIGNAL('update'),
                self.updateBar)
        QtCore.QObject.connect(self.mi_thread, QtCore.SIGNAL('finished()'),
                self.updateStatus)

    def ChgDirBtnClk(self):
        self.rootDir = QtGui.QFileDialog.getExistingDirectory(self, ("Choose Directory"), self.root_path, QtGui.QFileDialog.ShowDirsOnly | QtGui.QFileDialog.DontResolveSymlinks)
        if not self.DstDir:
            print "null"
        self.root_path = str(self.rootDir).encode('utf-8')
        self.treeDir.filltreeDir(self.root_path)
        
    def ChgDstDirBtnClk(self):
        self.DstDir = QtGui.QFileDialog.getExistingDirectory(self, ("Choose Directory"), self.dest_path, QtGui.QFileDialog.ShowDirsOnly | QtGui.QFileDialog.DontResolveSymlinks)
        self.dest_path = str(self.DstDir).encode('utf-8')
        self.DstFolder.setText("Destination folder: "+self.dest_path)

    def pushButtonRightClk(self):
        base_path = self.AddCurrentItem(self.treeDir.currentItem())
        if self.chkSubDir.isChecked() is True:
            for k, v in self.treeDir.getIds().iteritems():
                if k.startswith(base_path) and not base_path == k:
                    self.AddCurrentItem(v)

    def pushButtonLeftClk(self):
        if self.lstSelectedDir.currentItem() is not None:
            reply = QtGui.QMessageBox.question(self, 'Remove Item', "Are you sure to remove this item?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
            if reply == QtGui.QMessageBox.Yes:
                self.TotalQty -= count_files(self.lstSelectedDir.currentItem().text())
                self.sb.showMessage('Photo Selected: '+str(self.TotalQty))
                self.DirList.remove(self.lstSelectedDir.currentItem().text())
                self.lstSelectedDir.takeItem(self.lstSelectedDir.row(self.lstSelectedDir.currentItem()))
        
    def pushButtonClrClk(self):
        if self.lstSelectedDir.count() > 0:
            reply = QtGui.QMessageBox.question(self, 'Clear List', "Are you sure to remove ALL items?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
            if reply == QtGui.QMessageBox.Yes:
                self.lstSelectedDir.clear()
                self.DirList = []
                self.TotalQty = 0
                self.sb.showMessage('Photo Selected: '+str(self.TotalQty))
                    
    def CpyFileBtnClk(self):
        self.mi_thread.render(self.lstSelectedDir, self.dest_path, self.TotalQty)
    
    def updateBar(self, n):
        self.pb.show()
        self.pb.setRange(0, self.TotalQty)
        self.pb.setValue(n)
        self.sb.showMessage(self.tr("Copying photo: "+str(n)+" of "+str(self.TotalQty)))
    
    def updateStatus(self):
        self.pb.hide()
        self.sb.showMessage('Ready')
        
    def AddCurrentItem(self, currentItem):
        for k, v in self.treeDir.getIds().iteritems():
            if currentItem == v:
                if k not in self.DirList:
                    self.DirList.append(k)
                    self.lstSelectedDir.addItem(k)
                    self.TotalQty += count_files(k)
                    self.sb.showMessage('Photo Selected: '+str(self.TotalQty))
                else:
                    msg = "The directory '"+k+"' already exist into the list"
                    reply = QtGui.QMessageBox.information(self, 'Warning', msg, QtGui.QMessageBox.Ok)
                return k
            
    def ConfigurationW(self):
        self.configw = ConfigWindow()
        self.configw.show()
    
class treeDir(QtGui.QTreeWidget):
    def __init__(self, parent, rootDir):
        super(treeDir, self).__init__(parent)
        self.inittreeDir(rootDir)
        self.filltreeDir(rootDir)
                
    def inittreeDir(self, columnlabel):
        self.setGeometry(QtCore.QRect(10, 50, 256, 361))
        self.setColumnCount(1)
        self.header().hide()
        
    def filltreeDir(self, rootDir):
        self.clear()
        self.ids = {rootDir : QtGui.QTreeWidgetItem(self, (rootDir,))}
        for (root, dirs, files) in os.walk(rootDir):
            if re.match(r'^[^\..]+$' ,root):
                for d in dirs:
                    if re.match(r'^[^\..]+$' ,d):
                        root_deco = root.decode('utf-8')
                        d_deco = d.decode('utf-8')
                        fullpath = os.path.join(root_deco, d_deco)
                        self.ids[fullpath] = QtGui.QTreeWidgetItem(self.ids[root_deco], (d_deco,))
    
    def getIds(self):
        return self.ids


class WorkThread(QtCore.QThread):
    def render(self, lista, destino, cant):
        self.lista = lista
        self.dest = destino
        self.qty = 0
        self.total = cant
        self.start()
    

    def run(self):
        for index in xrange(self.lista.count()):
            src_path = str(self.lista.item(index).text().toUtf8()).decode('utf-8')
            for filename in os.listdir(src_path):
                if re.match(r'.*\.jpg$', filename, re.I):
                    self.qty += 1
                    self.emit(QtCore.SIGNAL('update'), self.qty)
                    try:
                        file = os.path.join(src_path, filename)
                        metadata = pyexiv2.ImageMetadata(file)
                        metadata.read()
                        tag = metadata['Exif.Photo.DateTimeOriginal']
                        year = tag.value.strftime('%Y')
                        month = tag.value.strftime('%m')
                        dest_fullpath = os.path.join(self.dest, year, month)
                        if not os.path.isdir(dest_fullpath):
                            os.makedirs(dest_fullpath)
                        shutil.copy2(file, dest_fullpath)
                    except KeyError:
                        file = os.path.join(src_path, filename)
                        dest_fullpath = os.path.join(self.dest, "without_date")
                        if not os.path.isdir(dest_fullpath):
                            os.makedirs(dest_fullpath)
                        shutil.copy2(file, dest_fullpath)
                    except:
                        raise


class ConfigWindow(QtGui.QWidget):
    def __init__(self):
        super(ConfigWindow, self).__init__()
        self.initUI()
                
    def initUI(self):
        self.setGeometry(200, 200, 200, 200)
        self.setWindowTitle(__name_app__+" Config")
        

def main():
    
    app = QtGui.QApplication(sys.argv)
    MainWin = MainWindows()
    
    MainWin.show()
        
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()