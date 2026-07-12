import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: window
    visible: true
    width: 960
    height: 720
    minimumWidth: 620
    minimumHeight: 500
    title: "Ghost"
    color: "#111315"

    ListModel {
        id: messages
        ListElement {
            sender: "Ghost"
            body: "What would you like to do?"
            isUser: false
            isError: false
        }
    }

    function submitMessage() {
        var message = composer.text.trim()
        if (!message || chat.busy)
            return

        messages.append({ "sender": "You", "body": message, "isUser": true, "isError": false })
        composer.clear()
        chat.send(message)
        conversation.positionViewAtEnd()
    }

    Connections {
        target: chat

        function onMessageReceived(message) {
            messages.append({ "sender": "Ghost", "body": message, "isUser": false, "isError": false })
            conversation.positionViewAtEnd()
        }

        function onRequestFailed(message) {
            messages.append({ "sender": "Connection error", "body": message, "isUser": false, "isError": true })
            conversation.positionViewAtEnd()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 76
            color: "#191d20"

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 28
                anchors.rightMargin: 28
                spacing: 14

                Rectangle {
                    Layout.preferredWidth: 34
                    Layout.preferredHeight: 34
                    radius: 6
                    color: "#20c997"

                    Text {
                        anchors.centerIn: parent
                        text: "G"
                        color: "#10211d"
                        font.bold: true
                        font.pixelSize: 18
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1

                    Label {
                        text: "Ghost"
                        color: "#f1f4f1"
                        font.pixelSize: 18
                        font.bold: true
                    }

                    Label {
                        text: chat.busy ? "Working" : "Ready"
                        color: chat.busy ? "#f3bf5b" : "#93d9c5"
                        font.pixelSize: 12
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#111315"

            ListView {
                id: conversation
                anchors.fill: parent
                anchors.margins: 28
                clip: true
                model: messages
                spacing: 14
                boundsBehavior: Flickable.StopAtBounds

                delegate: Item {
                    width: conversation.width
                    height: bubble.implicitHeight

                    Rectangle {
                        id: bubble
                        width: Math.min(implicitWidth, parent.width * 0.78)
                        implicitWidth: messageText.implicitWidth + 32
                        implicitHeight: messageColumn.implicitHeight + 24
                        anchors.right: isUser ? parent.right : undefined
                        radius: 6
                        color: isError ? "#4d292b" : (isUser ? "#176a58" : "#22272a")

                        Column {
                            id: messageColumn
                            anchors.fill: parent
                            anchors.margins: 16
                            spacing: 5

                            Text {
                                text: sender
                                color: isError ? "#ffb4ac" : (isUser ? "#d7fff2" : "#a7b4ae")
                                font.pixelSize: 12
                                font.bold: true
                            }

                            Text {
                                id: messageText
                                width: Math.min(implicitWidth, conversation.width * 0.78 - 32)
                                text: body
                                wrapMode: Text.Wrap
                                color: "#f1f4f1"
                                font.pixelSize: 15
                                lineHeight: 1.3
                            }
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 112
            color: "#191d20"

            RowLayout {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 12

                TextArea {
                    id: composer
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    enabled: !chat.busy
                    placeholderText: "Message Ghost"
                    placeholderTextColor: "#77817c"
                    color: "#f1f4f1"
                    font.pixelSize: 15
                    wrapMode: TextEdit.Wrap
                    selectByMouse: true
                    background: Rectangle {
                        radius: 6
                        color: "#111315"
                        border.color: composer.activeFocus ? "#20c997" : "#3d4743"
                        border.width: 1
                    }
                    Keys.onReturnPressed: function(event) {
                        if (!(event.modifiers & Qt.ShiftModifier)) {
                            submitMessage()
                            event.accepted = true
                        }
                    }
                }

                Button {
                    Layout.alignment: Qt.AlignBottom
                    Layout.preferredWidth: 90
                    Layout.preferredHeight: 42
                    text: chat.busy ? "Sending" : "Send"
                    enabled: composer.text.trim().length > 0 && !chat.busy
                    onClicked: submitMessage()

                    contentItem: Text {
                        text: parent.text
                        color: parent.enabled ? "#10211d" : "#7b8580"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.bold: true
                    }
                    background: Rectangle {
                        radius: 6
                        color: parent.enabled ? "#20c997" : "#2c3431"
                    }
                }
            }
        }
    }
}
