from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtCore import Qt, pyqtSignal, QAbstractItemModel


########################################
#
########################################
class MyTableWidget(QTableWidget):

    dragStarted = pyqtSignal(Qt.DropAction)
    itemsDropped = pyqtSignal(list, bool)
    deletePressed = pyqtSignal()

    ########################################
    #
    ########################################
#    def __init__(self, parent=None):
#        super().__init__(parent)

    ########################################
    #
    ########################################
    def dragEnterEvent(self, e):
#        print('TABLE dragEnterEvent')
        #if e.source() is None and e.mimeData().hasUrls():
        if e.mimeData().hasUrls():
            e.accept()

    ########################################
    #
    ########################################
    def dragMoveEvent(self, e):
#        print('TABLE dragMoveEvent')
#        if e.mimeData().hasUrls():
        e.accept()

    ########################################
    # TODO
    ########################################
    def dropEvent(self, e):
#        print('TABLE dropEvent')
#        print('DROP', e.mimeData())
#        if e.mimeData().hasUrls():

        e.accept()
        self.itemsDropped.emit(e.mimeData().urls(), e.source() is None)

    ########################################
    #
    ########################################
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.deletePressed.emit()
#            row = self.currentRow()
#            self.removeRow(row)
#        else:
#            super().keyPressEvent(event)

    ########################################
    #
    ########################################
    def startDrag(self, drop_actions):
#        print('startDrag', int(drop_actions))
#        if self.item(self.currentRow(), 0).text() != '..':
#         self.setMouseTracking(True)
        self.dragStarted.emit(drop_actions)

#     def mouseMoveEvent(self, e):
#         print('MOVE')
#         super().mouseMoveEvent(e)
#
#     def mouseReleaseEvent(self, event):
#         print('RELEASE')



