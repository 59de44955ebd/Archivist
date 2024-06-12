import os
import shutil
import subprocess
import sys
import traceback
import uuid

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import uic

APP_NAME = 'Archivist'  # Archivist QPy7zipExplorer
APP_VERSION = '0.1'

IS_FROZEN = getattr(sys, "frozen", False)

IS_WIN = sys.platform == 'win32'
IS_MAC = sys.platform == 'darwin'
if not IS_WIN and not IS_MAC:
    sys.exit(1)

# Use win32api on Windows because the pynput and mouse packages cause lag
# https://github.com/moses-palmer/pynput/issues/390
if IS_WIN:
    from ctypes import windll, create_unicode_buffer, byref
    from ctypes.wintypes import POINT, DWORD
    import psutil
    import tempfile

    user32 = windll.user32

    def mouse_pressed():
        return user32.GetKeyState(0x01) not in [0, 1]

    APP_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)))
    RES_DIR = os.path.realpath(os.path.join(APP_DIR, 'resources'))
    BIN_7ZIP = os.path.join(APP_DIR, 'resources', 'bin', 'win', '7z.exe')
    TMP_DIR = os.path.join(tempfile.gettempdir(), APP_NAME)
    EOL = chr(13) + chr(10)
else:
    if IS_FROZEN:
        APP_DIR = os.path.dirname(os.path.realpath(sys.executable))
        RES_DIR = os.path.realpath(os.path.join(APP_DIR, '..', 'Resources'))
    else:
        APP_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)))
        RES_DIR = os.path.realpath(os.path.join(APP_DIR, 'resources'))

    BIN_7ZIP = os.path.join(RES_DIR, 'bin', 'macos', '7zz')
    TMP_DIR = f'/tmp/{APP_NAME}'
    EOL = chr(10)

if os.path.isdir(TMP_DIR):
    shutil.rmtree(TMP_DIR, ignore_errors=True)
os.makedirs(TMP_DIR, exist_ok=True)

SUPPORTED_FORMATS = (
        '7z', 'APM', 'AR', 'ARJ', 'BZIP2', 'CAB', 'CHM', 'COMPOUND', 'CPIO', 'CramFS', 'DMG', 'Ext', 'FAT',
        'GZIP', 'HFS', 'HXS', 'iHEX', 'ISO', 'LZH', 'LZMA', 'MBR', 'MBR', 'MsLZ', 'Mub', 'NSIS', 'NTFS',
        'PPMD', 'QCOW2', 'RAR', 'RPM', 'SquashFS', 'TAR', 'UDF', 'UEFIc', 'UEFIs', 'VDI', 'VHD', 'VMDK',
        'WIM', 'XAR', 'XZ', 'Z', 'ZIP')

SUPPORTED_EXTENSIONS = (
        '7z', 'a', 'apk', 'apm', 'ar', 'arj', 'bz2', 'bzip2', 'cab', 'chi', 'chm', 'chq', 'chw', 'cpio', 'cramfs',
        'deb', 'dmg', 'doc', 'docx', 'epub', 'esd', 'exe', 'ext', 'ext2', 'ext3', 'ext4', 'fat', 'gz', 'gzip',
        'hfs', 'hfsx', 'hxi', 'hxq', 'hxr', 'hxs', 'hxw', 'ihex', 'img', 'iso',
        'jar', 'lha', 'lib', 'lit', 'lzh', 'lzma', 'mbr', 'msi', 'mslz', 'msp', 'mub', 'nsis',
        'ntfs', 'ods', 'odt', 'pkg', 'ppmd', 'ppt', 'qcow', 'qcow2', 'qcow2c', 'r00', 'rar', 'rpm', 'scap',
        'squashfs', 'swm', 'tar', 'taz', 'tbz', 'tbz2', 'tgz', 'tlz', 'txz', 'udf', 'uefif', 'vdi', 'vhd', 'vmdk',
        'whl', 'wim', 'xar', 'xls', 'xlsx', 'xpi', 'xz', 'z', 'zip', 'zipx')

FILTER_SUPPORTED = 'Supported Files (*.' + ' *.'.join(SUPPORTED_EXTENSIONS) + ');;All Files (*)'

EDITABLE_EXTENSIONS = ('7z', 'bz2', 'bzip2', 'tbz2', 'tbz', 'gz', 'gzip', 'tgz', 'tar', 'xz',
        'txz', 'zip', 'zipx', 'jar', 'xpi', 'odt', 'ods', 'docx', 'xlsx', 'epub')
# tar.bz2 tar.gz tar.lzma tar.xz

#7z 	X 	7z
#BZIP2 	X 	bz2 bzip2 tbz2 tbz
#GZIP 	X 	gz gzip tgz
#TAR 	X 	tar
#WIM 	X 	wim swm
#XZ 	X 	xz txz
#ZIP 	X 	zip zipx jar xpi odt ods docx xlsx epub

CREATABLE_EXTENSIONS = ('7z', 'zip', 'tar', 'tgz', 'tbz', 'txz')

#FILTER_CREATABLE = ';;'.join([f.upper() + ' archive (*.' + f + ')' for f in CREATABLE_EXTENSIONS])

FILTER_CREATABLE = ';;'.join((
    '7-Zip archive (*.7z)',
    'ZIP archive (*.zip)',
    'TAR archive (*.tar)',
    'TGZ archive (*.tgz *.tar.gz)',
    'TBZ archive (*.tbz *.tar.bz2)',
    'TXZ archive (*.txz *.tar.xz)',
))

COMPRESSION_ONLY_EXTENSIONS = ('bz2', 'bzip2', 'gz', 'gzip', 'xz', 'z', 'hxq', 'lzma')
# BUT: tar.lzma (tlz)

COL_NAME = 0
COL_SIZE = 1
COL_DATE = 2
COL_ATTR = 3

sort_descending = False

########################################
#
########################################
def format_filesize(num):
    k = 1024 if IS_WIN else 1000
    if num < k:
        return f'{num} B'
    for unit in ['KB','MB','GB','TB','PB','EB','ZB']:
        num /= k
        if abs(num) < k:
            return '%3.1f %s' % (num, unit)
    return '%.1f %s' % (num, 'YB')


########################################
# win only
########################################
class DelayedMimeData(QMimeData):

    def __init__(self):
        super().__init__()
        self.callbacks = []

    def add_callback(self, callback):
        self.callbacks.append(callback)

    def retrieveData(self, mime_type: str, preferred_type: QVariant.Type):
        if self.callbacks and not mouse_pressed():
            # check if explorer window
            p = QCursor.pos()
            hwnd = windll.user32.WindowFromPoint(POINT(p.x(), p.y()))
            pid = DWORD()
            user32.GetWindowThreadProcessId(hwnd, byref(pid))
            if psutil.Process(pid.value).name().lower() == 'explorer.exe':
                for callback in self.callbacks.copy():
                    self.callbacks.remove(callback)
                    callback()

        return QMimeData.retrieveData(self, mime_type, preferred_type)


########################################
#
########################################
class MyFreezableItem(QTableWidgetItem):

    def __init__(self, is_frozen=False):
        QTableWidgetItem.__init__(self)
        self.is_frozen = is_frozen

    def __lt__(self, other_item):
        if self.is_frozen:
            return not sort_descending
        elif other_item.is_frozen:
            return sort_descending
        return self.text() < other_item.text()


########################################
#
########################################
class MyFileNameItem(QTableWidgetItem):

    def __init__(self, is_frozen=False):
        QTableWidgetItem.__init__(self)
        self.is_frozen = is_frozen

    def __lt__(self, other_item):
        if self.is_frozen:
            return not sort_descending
        elif other_item.is_frozen:
            return sort_descending

        is_dir = self.data(Qt.UserRole + 1)
        other_is_dir = other_item.data(Qt.UserRole + 1)

        if is_dir and not other_is_dir:
            return True
        elif not is_dir and other_is_dir:
            return False
        else:
            return self.text().lower() < other_item.text().lower()


########################################
#
########################################
class MyFileSizeItem(QTableWidgetItem):

    def __init__(self, is_frozen=False):
        QTableWidgetItem.__init__(self)
        self.is_frozen = is_frozen
        self.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def __lt__(self, other_item):
        if self.is_frozen:
            return not sort_descending  #False if sort_descending else True
        elif other_item.is_frozen:
            return sort_descending  #True if sort_descending else False
        return self.data(Qt.UserRole) < other_item.data(Qt.UserRole)


########################################
#
########################################
class Main(QMainWindow):

    ########################################
    #
    ########################################
    def __init__ (self, app):
        super().__init__()

        self._settings = QSettings('fx', APP_NAME)

        self._current_archive = None
        self._current_ext = None  # NOT USED
        self._current_path = ''
        self._is_editable = False
        self._is_compressed_tar = False
        self._tmp_tar = None

#        self._eliminate_root_folder = self._settings.value('EliminateDuplication', False) == 'true'
#        self._extract_to_archive_folder = self._settings.value('AlwaysExtract', False) == 'true'
#        self._confirm_add = self._settings.value('ConfirmAdd', True) == 'true'
#        self._confirm_delete = self._settings.value('ConfirmDelete', True) == 'true'

        QResource.registerResource(os.path.join(RES_DIR, 'main.rcc'))
        uic.loadUi(os.path.join(RES_DIR, 'main.ui'), self)

        if IS_MAC and IS_FROZEN:
            app.fileOpened.connect(self._load_archive)

        # menu
        self.actionOpenArchive.triggered.connect(self.slot_load_archive)
        self.actionNewArchive.triggered.connect(self.slot_new_archive)

        self.actionEliminateDuplication.setChecked(self._settings.value('EliminateDuplication', False) == 'true')
        self.actionEliminateDuplication.toggled.connect(lambda flag:
                self._settings.setValue('EliminateDuplication', flag))

        self.actionAlwaysExtract.setChecked(self._settings.value('AlwaysExtract', False) == 'true')
        self.actionAlwaysExtract.toggled.connect(lambda flag:
                self._settings.setValue('AlwaysExtract', flag))

        self.actionConfirmAdd.setChecked(self._settings.value('ConfirmAdd', True) == 'true')
        self.actionConfirmAdd.toggled.connect(lambda flag:
                self._settings.setValue('ConfirmAdd', flag))

        self.actionConfirmDelete.setChecked(self._settings.value('ConfirmDelete', True) == 'true')
        self.actionConfirmDelete.toggled.connect(lambda flag:
                self._settings.setValue('ConfirmDelete', flag))

        self.actionAbout.triggered.connect(self.slot_about)

        # toolbar
        self.actionAdd.triggered.connect(self.slot_add)
        self.actionExtract.triggered.connect(self.slot_extract)
        self.actionTest.triggered.connect(self.slot_test)
        self.actionMove.triggered.connect(self.slot_move)
        self.actionDelete.triggered.connect(self.slot_delete)
        self.actionInfo.triggered.connect(self.slot_about)

        self._status_label = QLabel(self)
        self.statusbar.addPermanentWidget(self._status_label)

        self.tableWidget.setColumnWidth(1, 80)
        self.tableWidget.setColumnWidth(2, 160)
        self.tableWidget.setColumnWidth(3, 60)
        self.tableWidget.setColumnWidth(0, self.width() - 300 - 50)

        self.tableWidget.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)
        self.tableWidget.horizontalHeaderItem(1).setTextAlignment(Qt.AlignRight)
        self.tableWidget.horizontalHeaderItem(3).setTextAlignment(Qt.AlignRight)

        self.tableWidget.itemDoubleClicked.connect(self.slot_item_double_clicked)
        self.tableWidget.sortItems(0, Qt.AscendingOrder)

        self.tableWidget.customContextMenuRequested.connect(self.slot_context_menu_requested)

        self._context_menu = QMenu(self)

        self.action_extract = QAction('Extract', self._context_menu)
        self.action_extract.triggered.connect(self.slot_save)
        self._context_menu.addAction(self.action_extract)

        self._context_menu.addSeparator()

        self.action_open = QAction('Open', self._context_menu)
        self.action_open.triggered.connect(self.slot_open)
        self._context_menu.addAction(self.action_open)

#        self.action_view = QAction('View', self._context_menu)
#        self.action_view.triggered.connect(self.slot_view)
#        self._context_menu.addAction(self.action_view)

        self.action_edit = QAction('Edit', self._context_menu)
        self.action_edit.triggered.connect(self.slot_edit)
        self._context_menu.addAction(self.action_edit)

        self._context_menu.addSeparator()

        self.action_rename = QAction('Rename', self._context_menu)
        self.action_rename.triggered.connect(self.slot_rename)
        self._context_menu.addAction(self.action_rename)

        self.action_move = QAction('Move', self._context_menu)
        self.action_move.triggered.connect(self.slot_move)
        self._context_menu.addAction(self.action_move)

        self.action_delete = QAction('Delete', self._context_menu)
        self.action_delete.triggered.connect(self.slot_delete)
        self._context_menu.addAction(self.action_delete)

        self._context_menu.addSeparator()

        self.action_new_folder = QAction('New Folder', self._context_menu)
        self.action_new_folder.triggered.connect(self.slot_new_folder)
        self._context_menu.addAction(self.action_new_folder)

        self.tableWidget.dragStarted.connect(self.slot_table_drag_started)
        self.tableWidget.itemsDropped.connect(self.slot_table_items_dropped)
        self.tableWidget.deletePressed.connect(self.slot_delete)

        def _sort_changed(idx, order):
            global sort_descending
            sort_descending = order == Qt.DescendingOrder
            self.tableWidget.sortItems(idx, order)
        self.tableWidget.horizontalHeader().sortIndicatorChanged.connect(_sort_changed)

        self._icon_provider = QFileIconProvider()
        self._icon_folder = self._icon_provider.icon(QFileIconProvider.Folder)
        self._icon_file = self._icon_provider.icon(QFileIconProvider.File)

        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self.slot_edited_file_changed)
        self._watch_dir = uuid.uuid4().hex
        os.makedirs(os.path.join(TMP_DIR, self._watch_dir), exist_ok=True)
        self._edit_dict = {}

        self.show()

        if len(sys.argv) > 1:
            self._load_archive(sys.argv[1])

    ########################################
    # TODO: check if readonly!
    ########################################
    def _load_archive(self, fn):
        fn = os.path.normpath(fn)
        bn, ext = os.path.splitext(fn)
        ext = ext[1:].lower()

        if ext not in SUPPORTED_EXTENSIONS:
            # show message
            return

        is_compressed_tar = bn.lower().endswith('.tar')
        if ext in COMPRESSION_ONLY_EXTENSIONS and not is_compressed_tar:
            # show message
            return

        if self._current_archive:
            self._unload_archive()

        archive = os.path.realpath(fn)
        is_compressed_tar = is_compressed_tar or ext in ('tbz', 'tgz', 'tlz', 'txz')

        if ext == 'exe':
            # check if 7z sfx (7z can't edit/save ZIP sfx)
            if IS_WIN:
                command = [BIN_7ZIP, 't', archive]
            else:
                command = f"'{BIN_7ZIP}' t '{archive}'"
            output = self._run(command, return_stdout=True)
            is_editable = 'Type = 7z' in output
        else:
            is_editable = (is_compressed_tar and ext in ('bz2', 'gz', 'xz')) or ext in EDITABLE_EXTENSIONS

        ok = self._load_path(archive, '', is_editable, is_compressed_tar)

        self.tableWidget.setEnabled(ok)

        if ok:
            self._current_archive = archive
            self._current_ext = ext
            self._current_path = ''
            self._is_editable = is_editable
            self._is_compressed_tar = is_compressed_tar

            self.statusbar.showMessage('Archive successfully loaded.')
            self._status_label.setText(f'Archive editable: {"yes" if self._is_editable else "no"}')
            self.setWindowTitle(os.path.basename(fn) + ' - ' + APP_NAME)

        else:
            self.statusbar.showMessage('Error: failed to open archive.')
            self.setWindowTitle(APP_NAME)

        self._update_toolbar()

    ########################################
    #
    ########################################
    def _create_archive(self, fn):

        if self._current_archive:
            self._unload_archive()

        bn, ext = os.path.splitext(fn)
        ext = ext[1:].lower()
        is_tar = bn.lower().endswith('.tar')
        is_compressed_tar = is_tar or ext in ('tbz', 'tgz', 'tlz', 'txz')

        # currently asumes that this NEVER fails (TODO)
        if is_compressed_tar:
            tmp_tar = os.path.join(TMP_DIR, os.path.basename(bn) + '.tar')
            command = [BIN_7ZIP, 'a', self._tmp_tar, f"-xr!*"]
            self._run(command)
            command = [BIN_7ZIP, 'a', fn, tmp_tar]
            self._run(command)
        else:
            if IS_WIN:
                command = [BIN_7ZIP, 'a', fn, f"-xr!*"]
            else:
                command = f"'{BIN_7ZIP}' a '{fn}' -x'!*'"
            self._run(command)

        self._current_archive = os.path.realpath(fn)
        self._current_ext = ext
        self._current_path = ''
        self._is_editable = True
        self._is_compressed_tar = is_compressed_tar
        if is_compressed_tar:
            self._tmp_tar = tmp_tar

        self.tableWidget.cellChanged.connect(self.slot_item_edited)

        ok = self._load_path()
        self.tableWidget.setEnabled(ok)

        if ok:
            self.statusbar.showMessage('Archive successfully created.')
            self.setWindowTitle(os.path.basename(fn) + ' - ' + APP_NAME)
            self._update_toolbar()
        else:
            self.statusbar.showMessage('Error: failed to create archive.')
            self.setWindowTitle(APP_NAME)

        self._update_toolbar()

    ########################################
    #
    ########################################
    def _unload_archive(self):
        watched_files = self._watcher.files()
        if watched_files:
#            print('watched_files', watched_files)
            self._watcher.removePaths(watched_files)
            self._edit_dict = {}
            def _cleanup():
                for fn in watched_files:
                    os.unlink(fn)
            QTimer.singleShot(100, _cleanup)  # fails if called directly

        if self._tmp_tar:
            os.remove(self._tmp_tar)
            self._tmp_tar = None

        if self.tableWidget.receivers(self.tableWidget.cellChanged):
            self.tableWidget.cellChanged.disconnect(self.slot_item_edited)

#        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)

        self.lineEditPath.setText('')
        self._status_label.setText('')

        self._current_archive = None
        self._current_ext = None
        self._current_path = ''
        self._is_editable = False
        self._is_compressed_tar = False
        self._tmp_tar = None

    ########################################
    # for archives that don't store directories explicitely
    # returns list or None
    ########################################
    def _list_folders_implicit(self, archive, path, is_compressed_tar):

        if is_compressed_tar:
            if IS_WIN:
                command = f'"{BIN_7ZIP}" x "{archive}" -so | "{BIN_7ZIP}" l -si -ttar -ba -sccUTF-8 "{path}*"'
            else:
                command = f"'{BIN_7ZIP}' x '{archive}' -so | '{BIN_7ZIP}' l -si -ttar -ba -sccUTF-8 '{path}*'"
        else:
            if IS_WIN:
                command = [BIN_7ZIP, 'l', '-ba', '-sccUTF-8', archive, f"{path}*"]
            else:
                command = f"'{BIN_7ZIP}' l -ba -sccUTF-8 '{archive}' '{path}*'"

        output = self._run(command, return_stdout=True)
        if output == False:
            return
#        print(output)
        output = output[:-len(EOL)]
        if not output:
            return []

        rows = {}
        for line in output.split(EOL):
            filename = line[53:]
            if os.sep in filename[len(path):]:
                filename = filename[len(path):].split(os.sep)[0]
                if filename in rows:
                    continue
                size = 0
                attr = 'D'
                date_time = ''
            else:
                date_time = line[:19]
                attr = line[20:25].replace('.', '')
                size = int(line[26:38].strip() or 0)
                filename = filename.split(os.sep).pop()

            rows[filename] = [
                filename,
                size,
                date_time,
                attr,
            ]
        return rows.values()

    ########################################
    # for archives that store directories explicitely
    # returns list or None
    ########################################
    def _list_folders_explicit(self, archive, path, is_compressed_tar):
        rows = []

        if is_compressed_tar:
            if IS_WIN:
                command = f'"{BIN_7ZIP}" x "{archive}" -so | "{BIN_7ZIP}" l -ba -si -ttar -sccUTF-8 "{path}*" "-x!{path}*{os.sep}*'
            else:
                command = f"'{BIN_7ZIP}' x '{archive}' -so | '{BIN_7ZIP}' l -ba -si -ttar -sccUTF-8 '{path}*' -x'!{path}*{os.sep}*'"
        else:
            if IS_WIN:
                command = [BIN_7ZIP, 'l', '-ba', '-sccUTF-8', archive, f"{path}*", f"-x!{path}*{os.sep}*"]
            else:
                command = f"'{BIN_7ZIP}' l -ba -sccUTF-8 '{archive}' '{path}*' -x'!{path}*{os.sep}*'"

        output = self._run(command, return_stdout=True)
        if output == False:
            return
        output = output[:-len(EOL)]
#        print(output)
        if not output:
            return rows

        for line in output.split(EOL):
            date_time = line[:19]
            attr = line[20:25].replace('.', '')
            size = int(line[26:38].strip() or 0)
            filename = line[53:].split(os.sep).pop()

            rows.append([
                filename,
                size,
                date_time,
                attr,
            ])

        return rows

    ########################################
    #
    ########################################
    def _load_path(self, archive=None, path=None, is_editable=None, is_compressed_tar=None):

        if archive is None:
            archive = self._current_archive
        if path is None:
            path = self._current_path
        if is_editable is None:
            is_editable = self._is_editable
        if is_compressed_tar is None:
            is_compressed_tar = self._is_compressed_tar

        if path != '' and not path.endswith(os.sep):
            path += os.sep

#        if self._current_ext == '7z':
#            rows = self._list_folders_explicit(path)
#        else:

        rows = self._list_folders_implicit(archive, path, is_compressed_tar)  # self._current_ext == 'tar' or self._is_compressed_tar

        if rows is None:
            return False

        if self.tableWidget.receivers(self.tableWidget.cellChanged):
            self.tableWidget.cellChanged.disconnect(self.slot_item_edited)

        #self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)

        self.tableWidget.setSortingEnabled(False)

#        rows = sorted(rows, key = lambda i: i[COL_NAME].lower())

        if path != '':
            self.lineEditPath.setText(os.path.join(os.path.basename(archive), path))
            self.tableWidget.setRowCount(len(rows) + 1)

            flags = Qt.ItemIsEnabled  # | Qt.ItemIsSelectable

            item = MyFileNameItem(True)
            item.setText('..')
            item.setIcon(self._icon_folder)
            parts = path[:-1].split(os.sep)
            if len(parts) == 1:
                item.setData(Qt.UserRole, '')
            else:
                item.setData(Qt.UserRole, os.sep.join(parts[:-1]))
            item.setData(Qt.UserRole + 1, True)
            item.setFlags(flags)
            self.tableWidget.setItem(0, 0, item)

            item = MyFileSizeItem(True)
            item.setText('')
            item.setData(Qt.UserRole, -1)
            item.setFlags(flags)
            self.tableWidget.setItem(0, 1, item)

            for col in range(2, 4):
                item = MyFreezableItem(True)
                item.setFlags(flags)
                self.tableWidget.setItem(0, col, item)

            i = 1
        else:
            self.lineEditPath.setText(os.path.basename(archive) + os.sep)
            self.tableWidget.setRowCount(len(rows))
            i = 0

        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled

        for row in rows:

            # name
            item = MyFileNameItem()
            item.setText(row[COL_NAME])
            is_dir = 'D' in row[COL_ATTR]
            if is_dir:
                item.setIcon(self._icon_folder)
                item.setData(Qt.UserRole, path + row[COL_NAME])
            else:
                # get icon for file
                if IS_WIN:
                    ico = self._icon_provider.icon(QFileInfo(os.path.join(TMP_DIR, row[COL_NAME])))
                else: ico = self._icon_file
                item.setIcon(ico)
                item.setData(Qt.UserRole, path + row[COL_NAME])
            item.setFlags(flags | (Qt.ItemIsEditable if is_editable else Qt.NoItemFlags))
            item.setData(Qt.UserRole + 1, is_dir)
            self.tableWidget.setItem(i, 0, item)

            # size
            item = MyFileSizeItem()
            if is_dir:
                item.setText('')
                item.setData(Qt.UserRole, -1)
            else:
                item.setText(format_filesize(row[COL_SIZE]))
                item.setData(Qt.UserRole, row[COL_SIZE])
            item.setFlags(Qt.ItemIsEnabled)
            self.tableWidget.setItem(i, 1, item)

            # last modified
            item = MyFreezableItem()
            item.setText(row[COL_DATE])
            item.setFlags(Qt.ItemIsEnabled)
            self.tableWidget.setItem(i, 2, item)

            # attr
            item = MyFreezableItem()
            item.setText(row[COL_ATTR])
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item.setFlags(Qt.ItemIsEnabled)
            self.tableWidget.setItem(i, 3, item)

            i += 1

        self.tableWidget.setSortingEnabled(True)
#        self.tableWidget.sortItems(0, Qt.AscendingOrder)

        if is_editable:
            self.tableWidget.cellChanged.connect(self.slot_item_edited)

        return True

    ########################################
    #
    ########################################
    def _extract_archive(self, local_dir):
        if self._is_compressed_tar:
            if self._tmp_tar:
                if IS_WIN:
                    command = f'"{BIN_7ZIP}" x "{self._tmp_tar}" -aoa'
                else:
                    command = f"'{BIN_7ZIP}' x '{self._tmp_tar}' -aoa"
            else:
                if IS_WIN:
                    command = f'"{BIN_7ZIP}" x "{self._current_archive}" -so | "{BIN_7ZIP}" x -si -ttar -aoa'
                else:
                    command = f"'{BIN_7ZIP}' x '{self._current_archive}' -so | '{BIN_7ZIP}' x -si -ttar -aoa"
            self._run(command, cwd=local_dir)
        else:
            command = [BIN_7ZIP, 'x', '-aoa', '-spe' if self._settings.value('EliminateDuplication', False) == 'true' else '', self._current_archive]
            self._run(command, cwd=local_dir)

    ########################################
    #
    ########################################
    def _save_path(self, archive_path, local_dir, is_dir):
#        print('_save_path', archive_path, local_dir, is_dir)
        c = 'x' if is_dir else 'e'
        if self._is_compressed_tar:
            if self._tmp_tar:
                if IS_WIN:
                    command = f'"{BIN_7ZIP}" {c} "{self._tmp_tar}" -aoa "{archive_path}"'
                else:
                    command = f"'{BIN_7ZIP}' {c} '{self._tmp_tar}' -aoa '{archive_path}'"
            else:
                if IS_WIN:
                    # 7z x "D:\TMP\aaa.tar.gz" -so | 7z x -si -ttar aaa.txt
                    command = f'"{BIN_7ZIP}" x "{self._current_archive}" -so | "{BIN_7ZIP}" {c} -si -ttar -aoa "{archive_path}"'
                else:
                    command = f"'{BIN_7ZIP}' x '{self._current_archive}' -so | '{BIN_7ZIP}' {c} -si -ttar -aoa '{archive_path}'"
            self._run(command, cwd=local_dir)
        else:
            command = [BIN_7ZIP, c, '-aoa', self._current_archive, archive_path]
            self._run(command, cwd=local_dir)

    ########################################
    #
    ########################################
    def _delete_items(self):
        selected_items = [item for item in self.tableWidget.selectedItems() if item.column() == 0 and not item.is_frozen]
        if not selected_items:
            return
        if self._settings.value('ConfirmDelete', True) == 'true':
            if len(selected_items) > 1:
                title = 'Confirm Multiple File Delete'
                text = f'Are you sure you want to delete these {len(selected_items)} items?'
            elif selected_items[0].data(Qt.UserRole + 1):
                title = 'Confirm Folder Delete'
                text = f"Are you sure you want to delete the folder '{selected_items[0].text()}' and all its contents?"
            else:
                title = 'Confirm File Delete'
                text = f"Are you sure you want to delete '{selected_items[0].text()}'?"

            res = QMessageBox.question(self,
                    title,
                    text,
                    QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if res != QMessageBox.Ok:
                return
#        print([item.data(Qt.UserRole) for item in selected_items])
        command = [BIN_7ZIP, 'd', self._current_archive] + [item.data(Qt.UserRole) for item in selected_items]
        self._run(command)
        self._load_path()

    ########################################
    #
    ########################################
    def _add_items(self, files_folders):
        if not self._is_editable:
            return
        if self._settings.value('ConfirmAdd', True) == 'true':
            res = QMessageBox.question(self,
                    'Confirm File Copy',
                    f'Copy to:\n{self.lineEditPath.text()}\nAre you sure you want to copy files to archive?',
                    QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if res != QMessageBox.Ok:
                return

        tmp_paths = []
#        del_items = []
        rename_items = []

        for fn_src in files_folders:
            bn_src = os.path.basename(fn_src)

            # copy to tmp with random name
            bn_tmp = uuid.uuid4().hex
            fn_tmp = os.path.join(TMP_DIR, bn_tmp)

            if os.path.isdir(fn_src):
                shutil.copytree(fn_src, fn_tmp)
            elif os.path.isfile(fn_src):
                shutil.copyfile(fn_src, fn_tmp)
            else:
                continue

            tmp_paths.append(fn_tmp)
#            del_items.append(self._current_path + bn_src)
            rename_items += [bn_tmp, self._current_path + os.sep + bn_src]

        if not tmp_paths:
            return

        if self._is_compressed_tar:
            if self._tmp_tar is None:
                # unfortunately we have to unpack tar coompletely to tmp dir

                # find name of internal tar
                command = [BIN_7ZIP, 'l', '-ba', '-sccUTF-8', self._current_archive]
                output = self._run(command, return_stdout=True)
                if not output:
                    return
                tar_name = output.split(EOL)[0][53:]

                # unpack tar to tmp
                command = [BIN_7ZIP, 'e',  self._current_archive]
                self._run(command, cwd=TMP_DIR)
                tmp_tar = os.path.join(TMP_DIR, tar_name)
                if not os.path.isfile(tmp_tar):
                    return
                self._tmp_tar = tmp_tar

            # add to tar
            command = [BIN_7ZIP, 'a', self._tmp_tar] + tmp_paths
            self._run(command)

            # then rename
            command = [BIN_7ZIP, 'rn', self._tmp_tar] + rename_items
            self._run(command)

            # compress tar with same filename/format
            os.rename(self._current_archive, self._current_archive + '.__bak__')
            command = [BIN_7ZIP, 'a', self._current_archive, self._tmp_tar]
            self._run(command)
            os.unlink(self._current_archive + '.__bak__')

        else:
            # add to archive
            command = [BIN_7ZIP, 'a', self._current_archive] + tmp_paths
            self._run(command)

            # then rename
            # p2q0r2x2y2z2w2
            command = [BIN_7ZIP, 'rn', '-up1q0r2y2', self._current_archive] + rename_items
            self._run(command)

        self._clear_tmp_dir()
        self._load_path()

    ########################################
    #
    ########################################
    def _open_item(self, item):
        if item.data(Qt.UserRole + 1):
            path = item.data(Qt.UserRole)
            ok = self._load_path(path=path)
            if ok:
                self._current_path = path
        else:
            archive_path = item.data(Qt.UserRole)
            self._save_path(archive_path, TMP_DIR, False)
            fn = os.path.join(TMP_DIR, os.path.basename(archive_path))
            if IS_WIN:
                os.startfile(fn, 'open')
            else:
                subprocess.call(('open', fn))

    ########################################
    #
    ########################################
#    def _view_item(self, item):
#        archive_path = item.data(Qt.UserRole)
#        self._save_path(archive_path, TMP_DIR, False)
#        fn = os.path.join(TMP_DIR, os.path.basename(archive_path))
#        if IS_WIN:
#            os.startfile('notepad.exe', 'open', fn)
#        else:
#            subprocess.call(('open', fn))  # TODO

    ########################################
    #
    ########################################
    def _edit_item(self, item):
        archive_path = item.data(Qt.UserRole)

        if archive_path not in self._edit_dict.values():
            watch_tmp_dir = os.path.join(TMP_DIR, self._watch_dir, uuid.uuid4().hex)
            os.makedirs(watch_tmp_dir, exist_ok=True)

            self._save_path(archive_path, watch_tmp_dir, False)

            fn = os.path.join(watch_tmp_dir, os.path.basename(archive_path))

            self._edit_dict[fn] = archive_path
            self._watcher.addPath(fn)
        else:
            fn = list(self._edit_dict.keys())[list(self._edit_dict.values()).index(archive_path)]

        if IS_WIN:
#            os.startfile('notepad.exe', 'open', fn)
            try:
                os.startfile(fn, 'edit')
            except:
                os.startfile(fn, 'open')
        else:
            subprocess.call(('open', fn))  # TODO

    ########################################
    #
    ########################################
    def _clear_tmp_dir(self):
        for filename in os.listdir(TMP_DIR):
            file_path = os.path.join(TMP_DIR, filename)
            try:
                if os.path.isfile(file_path):  # or os.path.islink(file_path):
                    if file_path != self._tmp_tar:
                        os.unlink(file_path)
                elif os.path.isdir(file_path):
                    if file_path != self._watch_dir:
                        shutil.rmtree(file_path, ignore_errors=True)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

    ########################################
    #
    ########################################
    def _update_toolbar(self):
        if self._current_archive:
            self.actionAdd.setEnabled(self._is_editable)
            self.actionExtract.setEnabled(True)
            self.actionTest.setEnabled(True)
            self.actionMove.setEnabled(self._is_editable)
            self.actionDelete.setEnabled(self._is_editable)
        else:
            self.actionAdd.setEnabled(False)
            self.actionExtract.setEnabled(False)
            self.actionTest.setEnabled(False)
            self.actionMove.setEnabled(False)
            self.actionDelete.setEnabled(False)

    ########################################
    #
    ########################################
    def _run(self, command, cwd=None, return_stdout=False):
        try:
            if return_stdout:
                # This is equivalent to:
                # return run(..., check=True, stdout=PIPE).stdout
                return subprocess.check_output(command, cwd=cwd, shell=True).decode()
            else:
                subprocess.run(command,
                    stdout=subprocess.DEVNULL,
    #                stderr=subprocess.DEVNULL,
    #                stdin=subprocess.DEVNULL,
                    cwd=cwd,
                    shell=True
                    )
                return True
        except Exception as e:
            self.statusbar.showMessage(f'Error: {e}')
            return False

    def __EVENTS(): pass

    ########################################
    #
    ########################################
    def dragEnterEvent(self, e):
        #print('MAIN dragEnterEvent', e.source(), int(e.dropAction()))
        # source None means drop from outside (e.g. Explorer)
        if e.source() is None and e.mimeData().hasUrls():
            if os.path.splitext(e.mimeData().urls()[0].toLocalFile())[1][1:] in SUPPORTED_EXTENSIONS:
                e.accept()

    ########################################
    #
    ########################################
    def dropEvent(self, e):
#        print('MAIN dropEvent')
#        for u in e.mimeData().urls():
#            fn = os.path.normpath(u.toLocalFile())
#            if os.path.splitext(fn)[1][1:] in SUPPORTED_EXTENSIONS:
#                self._load_archive(fn)
#                break
        self._load_archive(os.path.normpath(e.mimeData().urls()[0].toLocalFile()))

	########################################
	#
	########################################
    def closeEvent(self, e):
        self._watcher.fileChanged.disconnect(self.slot_edited_file_changed)
        watched_files = self._watcher.files()
        if watched_files:
            self._watcher.removePaths(watched_files)
#            QTimer.singleShot(100, _cleanup)  # fails if called directly
        shutil.rmtree(TMP_DIR, ignore_errors=True)

    def __SLOTS(): pass

    ########################################
    #
    ########################################
    def slot_add(self):
        if not self._is_editable:
            return
        files, _ = QFileDialog.getOpenFileNames(self, 'Add Files')
        if files:
            self._add_items(files)

    ########################################
    #
    ########################################
    def slot_extract(self):
        if self._settings.value('AlwaysExtract', False) == 'true':
            target_dir = os.path.dirname(self._current_archive)
        else:
            target_dir = QFileDialog.getExistingDirectory(self, 'Select Destination', os.path.dirname(self._current_archive))
            if not target_dir:
                return
        selected_items = [item for item in self.tableWidget.selectedItems() if item.column() == 0 and not item.is_frozen]
        if selected_items:
            for item in selected_items:
                self._save_path(item.data(Qt.UserRole), target_dir, item.data(Qt.UserRole + 1))
        else:
            self._extract_archive(target_dir)

    ########################################
    #
    ########################################
    def slot_test(self):
        if IS_WIN:
            command = [BIN_7ZIP, 't', self._current_archive]
        else:
            command = f"'{BIN_7ZIP}' t '{self._current_archive}'"
        output = self._run(command, return_stdout=True)
        QMessageBox.information(self, APP_NAME, output)

    ########################################
    #
    ########################################
    def slot_item_edited(self, row, col):
#        if col != 0:
#            return
        item = self.tableWidget.item(row, col)
        old_name = item.data(Qt.UserRole).split(os.sep).pop()
        new_name = item.text()
        if new_name == old_name:
            return
        if new_name == '':
            # revert
            item.setText(old_name)
            return
        if IS_WIN:
            command = [BIN_7ZIP, 'rn', self._current_archive, self._current_path + old_name, self._current_path + new_name]
        else:
            command = f"'{BIN_7ZIP}' a '{self._current_archive}' '{rel_dir}'"
        self._run(command, cwd=TMP_DIR)
        self._load_path()

    ########################################
    #
    ########################################
    def slot_table_drag_started(self, drop_actions):
        drag = QDrag(self)
        dragged_items = [item for item in self.tableWidget.selectedItems() if item.column() == 0]
        path_list = []

        if IS_WIN:
            mime = DelayedMimeData()
            for dragged_item in dragged_items:
                archive_path = dragged_item.data(Qt.UserRole)
                is_dir = dragged_item.data(Qt.UserRole + 1)

                def write_to_file(archive_path=archive_path, is_dir=is_dir):
                    self._save_path(archive_path, TMP_DIR, is_dir)
                mime.add_callback(write_to_file)

                if is_dir:
                    d = os.path.join(TMP_DIR, dragged_item.data(Qt.UserRole))
                    path_list.append(QUrl.fromLocalFile(d))
                    os.mkdir(d)
                else:
                    fn = os.path.join(TMP_DIR, dragged_item.text())
                    with open(fn, 'w') as f:
                        f.write('')
                    path_list.append(QUrl.fromLocalFile(fn))

        else:
            mime = QMimeData()
            for dragged_item in dragged_items:
                archive_path = dragged_item.data(Qt.UserRole)
                is_dir = dragged_item.data(Qt.UserRole + 1)
                self._save_path(archive_path, TMP_DIR, is_dir)
                if is_dir:
                    d = os.path.join(TMP_DIR, dragged_item.data(Qt.UserRole))
                    path_list.append(QUrl.fromLocalFile(d))
                else:
                    fn = os.path.join(TMP_DIR, dragged_item.text())
                    path_list.append(QUrl.fromLocalFile(fn))

        mime.setUrls(path_list)
        mime.setData('application/x-qabstractitemmodeldatalist',
                     self.tableWidget.mimeData(self.tableWidget.selectedItems()).data('application/x-qabstractitemmodeldatalist'))
        drag.setMimeData(mime)

        drag.exec(Qt.MoveAction)  # segmentation fault

        # cleanup
#         time.sleep(2)
        # self._clear_tmp_dir()

#         super(QTableWidget, self.tableWidget).startDrag(drop_actions)

    ########################################
    #
    ########################################
    def slot_table_items_dropped(self, urls, is_external):
        if not is_external:
            self._clear_tmp_dir()
            return
        self._add_items([os.path.normpath(u.toLocalFile()) for u in urls])

    ########################################
    #
    ########################################
    def slot_load_archive(self):
        fn, _ = QFileDialog.getOpenFileName(self, 'Archive File', '', FILTER_SUPPORTED)
        if not fn:
            return
        self._load_archive(fn)

    ########################################
    #
    ########################################
    def slot_new_archive(self):
        fn, _ = QFileDialog.getSaveFileName(self, 'New Archive', '', FILTER_CREATABLE)
        if not fn:
            return
        ext = os.path.splitext(fn)[1][1:].lower()
        if ext in CREATABLE_EXTENSIONS:
            self._create_archive(fn)

    ########################################
    #
    ########################################
    def slot_about (self):
        seven_zip_ver = self._run(BIN_7ZIP, return_stdout=True).strip().split(EOL)[0]
        # SUPPORTED_FORMATS
        msg = f'''<b>{APP_NAME} v{APP_VERSION}</b><br><br>
        A simple <a href='https://www.7-zip.org/'>7-zip</a> GUI for macOS and Windows, based on <a href='https://doc.qt.io/qt-5/'>Qt 5</a> and <a href='https://www.python.org/'>Python 3</a><br><br>
        Currently used 7-zip cli version:<br>
        {seven_zip_ver}<br><br>
        Supported file types:<br>
        {", ".join(SUPPORTED_EXTENSIONS)}.<br><br>
        Editable file types:<br>
        {", ".join(EDITABLE_EXTENSIONS)}.<br><br>
        App on GitHub: <a href='https://github.com/59de44955ebd/{APP_NAME}'>{APP_NAME}</a><br>
        License for app\'s Python code: MIT
        '''
        QMessageBox.about(self, 'About', msg)

    ########################################
    #
    ########################################
    def slot_item_double_clicked(self, item):
        self._open_item(self.tableWidget.item(item.row(), 0))

    ########################################
    #
    ########################################
    def slot_context_menu_requested(self, pos):
        item = self.tableWidget.currentItem()
        is_selected = item is not None and self.tableWidget.item(item.row(), 0).text() != '..'
        is_folder = self.tableWidget.item(item.row(), 0).data(Qt.UserRole + 1)

        self.action_extract.setEnabled(is_selected)

        self.action_open.setEnabled(is_selected)
#        self.action_view.setEnabled(is_selected and not is_folder)
        self.action_edit.setEnabled(is_selected and not is_folder)

        self.action_rename.setEnabled(is_selected and self._is_editable)
        self.action_move.setEnabled(is_selected and self._is_editable)
        self.action_delete.setEnabled(is_selected and self._is_editable)

        self.action_new_folder.setEnabled(self._is_editable)

        self._context_menu.exec(QCursor.pos())

    ########################################
    #
    ########################################
    def slot_save(self):
        local_dir = QFileDialog.getExistingDirectory(self, 'Save to Folder', '', QFileDialog.ShowDirsOnly)
        if local_dir == '':
            return
        local_dir = os.path.normpath(local_dir)
        self.statusbar.showMessage('Saving files...')
        sel = self.tableWidget.selectedItems()
        for item in sel:
            if item.column() == 0:
                fn = item.data(Qt.UserRole)
                self._save_path(fn, local_dir, item.data(Qt.UserRole + 1))
        #self.statusbar.showMessage('Done.')

    ########################################
    #
    ########################################
    def slot_open(self):
        item = self.tableWidget.currentItem()
        self._open_item(self.tableWidget.item(item.row(), 0))

    ########################################
    #
    ########################################
#    def slot_view(self):
#        item = self.tableWidget.currentItem()
#        self._view_item(self.tableWidget.item(item.row(), 0))

    ########################################
    #
    ########################################
    def slot_edit(self):
        item = self.tableWidget.currentItem()
        self._edit_item(self.tableWidget.item(item.row(), 0))

    ########################################
    #
    ########################################
    def slot_edited_file_changed(self, filename):
#        print('TMPFILE', filename)  # C:\Users\fluxus\AppData\Local\Temp\Archivist\4ea58ef284834f8c8544f5d3e0171491\README.md
#        print('FILE IN ARCH', self._edit_dict[filename])  # README.md

#TMPFILE C:\Users\fluxus\AppData\Local\Temp\Archivist\dc0fa7de198b44b28b493a9027de2a7b\88450a779e534b1c8a9f5580ff744de2\version_res.txt
#FILE IN ARCH _test_files\version_res.txt

        if not os.path.isfile(filename):
            print('file deleted', filename)
            self._watcher.removePath(filename)
            del self._edit_dict[filename]
            return

        watch_dir = os.path.join(TMP_DIR, self._watch_dir)
        file_to_add = filename[len(watch_dir) + 1:]  # 88450a779e534b1c8a9f5580ff744de2\version_res.txt

        # add to archive, including random dir
        command = [BIN_7ZIP, 'a', self._current_archive, file_to_add]
        self._run(command, cwd=watch_dir)

        command = [BIN_7ZIP, 'rn', '-up1q0r2y2', self._current_archive, file_to_add, self._edit_dict[filename]]
#        print(command)
        self._run(command)

        self._load_path()

    ########################################
    #
    ########################################
    def slot_rename(self):
        if not self._is_editable:
            return
        item = self.tableWidget.currentItem()
        if item is None:
            return
        item = self.tableWidget.item(item.row(), 0)
        if item.is_frozen:
            return
        self.tableWidget.editItem(item)

    ########################################
    #
    ########################################
    def slot_move(self):
        if not self._is_editable:
            return
        item = self.tableWidget.currentItem()
        if item is None:
            return
        item = self.tableWidget.item(item.row(), 0)
        if item.is_frozen:
            return

        old_name = self._current_path + item.text()
        new_name, ok = QInputDialog.getText(self, 'New Name', 'Enter Name:', QLineEdit.Normal, old_name)
        if not new_name or new_name == old_name:
            return
        if IS_WIN:
            command = [BIN_7ZIP, 'rn', self._current_archive, old_name, new_name]
        else:
            command = f"'{BIN_7ZIP}' a '{self._current_archive}' '{rel_dir}'"

        self._run(command, cwd=TMP_DIR)
        self._load_path()

    ########################################
    #
    ########################################
    def slot_delete(self):
        if not self._is_editable:
            return
        self._delete_items()

    ########################################
    #
    ########################################
    def slot_new_folder(self):
        folder_name, ok = QInputDialog.getText(self, 'New Folder', 'Enter Folder Name:')
        if not folder_name:
            return
        rel_dir = self._current_path + folder_name
        abs_dir = os.path.join(TMP_DIR, rel_dir)
        os.makedirs(abs_dir, exist_ok=True)
        if IS_WIN:
            command = [BIN_7ZIP, 'a', self._current_archive, rel_dir]
        else:
            command = f"'{BIN_7ZIP}' a '{self._current_archive}' '{rel_dir}'"
        self._run(command, cwd=TMP_DIR)
        self._load_path()
        self._clear_tmp_dir()


########################################
# macos only
########################################
class MyApplication(QApplication):
    fileOpened = pyqtSignal(str)
    def event(self, e):
        if e.type() == QEvent.FileOpen:
            self.fileOpened.emit(e.file())
        return super().event(e)


########################################
#
########################################
if __name__ == '__main__':
    sys.excepthook = traceback.print_exception
    if IS_MAC and IS_FROZEN:
        app = MyApplication(sys.argv)
    else:
        app = QApplication(sys.argv)
    main = Main(app)
    sys.exit(app.exec())
