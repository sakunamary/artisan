# Form implementation generated from reading ui file 'ui/BlendDialog.ui'
#
# Created by: PyQt6 UI code generator 6.7.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_customBlendDialog(object):
    def setupUi(self, customBlendDialog):
        customBlendDialog.setObjectName("customBlendDialog")
        customBlendDialog.resize(563, 257)
        customBlendDialog.setWindowTitle("Dialog")
        customBlendDialog.setToolTip("")
        customBlendDialog.setAccessibleDescription("")
        self.verticalLayout = QtWidgets.QVBoxLayout(customBlendDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lineEdit_name = QtWidgets.QLineEdit(parent=customBlendDialog)
        font = QtGui.QFont()
        font.setBold(True)
        self.lineEdit_name.setFont(font)
        self.lineEdit_name.setToolTip("")
        self.lineEdit_name.setAccessibleDescription("")
        self.lineEdit_name.setInputMask("")
        self.lineEdit_name.setText("")
        self.lineEdit_name.setPlaceholderText("")
        self.lineEdit_name.setClearButtonEnabled(True)
        self.lineEdit_name.setObjectName("lineEdit_name")
        self.horizontalLayout.addWidget(self.lineEdit_name)
        self.label_weight = QtWidgets.QLabel(parent=customBlendDialog)
        self.label_weight.setToolTip("")
        self.label_weight.setAccessibleDescription("")
        self.label_weight.setText("Weight")
        self.label_weight.setObjectName("label_weight")
        self.horizontalLayout.addWidget(self.label_weight)
        self.lineEdit_weight = QtWidgets.QLineEdit(parent=customBlendDialog)
        self.lineEdit_weight.setMinimumSize(QtCore.QSize(70, 0))
        self.lineEdit_weight.setMaximumSize(QtCore.QSize(70, 16777215))
        self.lineEdit_weight.setToolTip("")
        self.lineEdit_weight.setAccessibleDescription("")
        self.lineEdit_weight.setInputMask("")
        self.lineEdit_weight.setText("")
        self.lineEdit_weight.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.lineEdit_weight.setPlaceholderText("")
        self.lineEdit_weight.setClearButtonEnabled(True)
        self.lineEdit_weight.setObjectName("lineEdit_weight")
        self.horizontalLayout.addWidget(self.lineEdit_weight)
        self.label_unit = QtWidgets.QLabel(parent=customBlendDialog)
        self.label_unit.setToolTip("")
        self.label_unit.setAccessibleDescription("")
        self.label_unit.setText("")
        self.label_unit.setObjectName("label_unit")
        self.horizontalLayout.addWidget(self.label_unit)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.tableWidget = QtWidgets.QTableWidget(parent=customBlendDialog)
        self.tableWidget.setToolTip("")
        self.tableWidget.setAccessibleDescription("")
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.verticalLayout.addWidget(self.tableWidget)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.pushButton_add = QtWidgets.QPushButton(parent=customBlendDialog)
        self.pushButton_add.setToolTip("")
        self.pushButton_add.setAccessibleDescription("")
        self.pushButton_add.setText("+")
        self.pushButton_add.setObjectName("pushButton_add")
        self.horizontalLayout_3.addWidget(self.pushButton_add)
        self.buttonBox = QtWidgets.QDialogButtonBox(parent=customBlendDialog)
        self.buttonBox.setToolTip("")
        self.buttonBox.setAccessibleDescription("")
        self.buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel|QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.horizontalLayout_3.addWidget(self.buttonBox)
        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.retranslateUi(customBlendDialog)
        self.buttonBox.accepted.connect(customBlendDialog.accept) # type: ignore
        self.buttonBox.rejected.connect(customBlendDialog.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(customBlendDialog)

    def retranslateUi(self, customBlendDialog):
        pass


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    customBlendDialog = QtWidgets.QDialog()
    ui = Ui_customBlendDialog()
    ui.setupUi(customBlendDialog)
    customBlendDialog.show()
    sys.exit(app.exec())
