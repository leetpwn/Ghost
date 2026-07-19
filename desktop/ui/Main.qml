import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: window

    visible: true
    width: 1100
    height: 720
    minimumWidth: 800
    minimumHeight: 550

    title: "Ghost"

    color: "#0d1117"

    ListModel {
        id: terminalOutput

        ListElement {
            text: "Ghost v0.4"
            isCommand: false
            isError: false
        }

        ListElement {
            text: "Model: qwen3:8b"
            isCommand: false
            isError: false
        }

        ListElement {
            text: "Type a command or ask anything."
            isCommand: false
            isError: false
        }

        ListElement {
            text: ""
            isCommand: false
            isError: false
        }
    }

    function runSlashCommand(command) {

    switch (command) {

    case "/help":

        terminalOutput.append({
            "text": "Commands:\n/help\n/clear\n/status\n/exit",
            "isCommand": false,
            "isError": false
        })

        return true

    case "/clear":

        terminalOutput.clear()

        terminalOutput.append({
            "text": "Ghost v0.4",
            "isCommand": false,
            "isError": false
        })

        terminalOutput.append({
            "text": "Terminal cleared.",
            "isCommand": false,
            "isError": false
        })

        return true

    case "/status":

        terminalOutput.append({
            "text":
                "Ghost Status\n\n" +
                "Model: qwen3:8b\n" +
                "Backend: Connected\n" +
                "Conversation: Active",
            "isCommand": false,
            "isError": false
        })

        return true

    case "/exit":

        Qt.quit()

        return true

    default:

        return false
    }
}

    function submitCommand() {

        var command = commandInput.text.trim()

        if (runSlashCommand(command)) {

            commandInput.clear()

            terminal.positionViewAtEnd()

            return
        }

        if (!command || chat.busy)
            return

        terminalOutput.append({
            "text": "> " + command,
            "isCommand": true,
            "isError": false
        })

        commandInput.clear()

        chat.send(command)

        terminal.positionViewAtEnd()
    }

    Connections {

        target: chat

        function onMessageReceived(message) {

            terminalOutput.append({
                "text": message,
                "isCommand": false,
                "isError": false
            })

            terminal.positionViewAtEnd()
        }

        function onRequestFailed(message) {

            terminalOutput.append({
                "text": message,
                "isCommand": false,
                "isError": true
            })

            terminal.positionViewAtEnd()
        }
    }

    ColumnLayout {

        anchors.fill: parent
        spacing: 0

        Rectangle {

            Layout.fillWidth: true
            Layout.preferredHeight: 48

            color: "#161b22"

            border.color: "#30363d"
            border.width: 1

            RowLayout {

                anchors.fill: parent

                anchors.leftMargin: 18
                anchors.rightMargin: 18

                Label {

                    text: "GHOST"

                    font.bold: true
                    font.pixelSize: 18

                    color: "#58a6ff"
                }

                Item {
                    Layout.fillWidth: true
                }

                Label {

                    text: "qwen3:8b"

                    color: "#8b949e"

                    font.family: "Consolas"
                }

                Rectangle {

                    width: 8
                    height: 8

                    radius: 4

                    color: chat.busy
                           ? "#f1c40f"
                           : "#3fb950"
                }

                Label {

                    text: chat.busy
                          ? "Thinking..."
                          : "Idle"

                    color: "#8b949e"

                    font.family: "Consolas"
                }
            }
        }

        Rectangle {

            Layout.fillWidth: true
            Layout.fillHeight: true

            color: "#0d1117"

            ListView {

                id: terminal

                anchors.fill: parent

                anchors.margins: 18

                spacing: 10

                clip: true

                model: terminalOutput

                boundsBehavior: Flickable.StopAtBounds

                delegate: Text {

                    width: terminal.width

                    text: model.text

                    wrapMode: Text.Wrap

                    font.family: "Consolas"

                    font.pixelSize: 15

                    lineHeight: 1.4

                    color: {
                        if (model.isError)
                            return "#ff7b72"

                        if (model.isCommand)
                            return "#58a6ff"

                        return "#e6edf3"
                    }
                }
            }
        }

                Rectangle {

            Layout.fillWidth: true
            Layout.preferredHeight: 60

            color: "#161b22"

            border.color: "#30363d"
            border.width: 1

            RowLayout {

                anchors.fill: parent

                anchors.leftMargin: 18
                anchors.rightMargin: 18
                spacing: 12

                Label {

                    text: ">"

                    color: "#58a6ff"

                    font.family: "Consolas"
                    font.pixelSize: 18
                    font.bold: true
                }

                TextArea {

                    id: commandInput

                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    enabled: !chat.busy

                    placeholderText: "Ask Ghost anything..."
                    placeholderTextColor: "#6e7681"

                    color: "#e6edf3"

                    font.family: "Consolas"
                    font.pixelSize: 15

                    wrapMode: TextEdit.Wrap

                    selectByMouse: true

                    background: Rectangle {
                        color: "transparent"
                    }

                    Keys.onReturnPressed: function(event) {

                        if (!(event.modifiers & Qt.ShiftModifier)) {
                            submitCommand()
                            event.accepted = true
                        }
                    }

                    Component.onCompleted: forceActiveFocus()
                }

                Label {

                    text: chat.busy
                          ? "RUNNING"
                          : "READY"

                    color: chat.busy
                           ? "#f1c40f"
                           : "#3fb950"

                    font.family: "Consolas"
                    font.pixelSize: 13
                    font.bold: true
                }
            }
        }

        Rectangle {

            Layout.fillWidth: true
            Layout.preferredHeight: 30

            color: "#0d1117"

            RowLayout {

                anchors.fill: parent

                anchors.leftMargin: 18
                anchors.rightMargin: 18

                Label {
                    text: "Enter Send"
                    color: "#6e7681"
                    font.family: "Consolas"
                    font.pixelSize: 12
                }

                Label {
                    text: "Shift+Enter New Line"
                    color: "#6e7681"
                    font.family: "Consolas"
                    font.pixelSize: 12
                }

                Item {
                    Layout.fillWidth: true
                }

                Label {
                    text: "Mach 4 • AI Terminal"
                    color: "#6e7681"
                    font.family: "Consolas"
                    font.pixelSize: 12
                }
            }
        }
            }
}