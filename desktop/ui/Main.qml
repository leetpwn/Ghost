import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: window

    visible: true
    width: 1100
    height: 720

    minimumWidth: 900
    minimumHeight: 550

    title: "Ghost"
    color: "#0d1117"

    property int currentPage: 0


    // =========================================================
    // TERMINAL MODEL
    // =========================================================

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


    // =========================================================
    // NETWORK MODEL
    // =========================================================

    ListModel {
        id: networkConnections
    }


    // =========================================================
    // TERMINAL COMMANDS
    // =========================================================

    function runSlashCommand(command) {

        switch (command) {

        case "/help":

            terminalOutput.append({
                "text":
                    "Commands:\n" +
                    "/help\n" +
                    "/clear\n" +
                    "/status\n" +
                    "/network\n" +
                    "/exit",
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
                    "Conversation: Active\n" +
                    "Network Monitor: Active",
                "isCommand": false,
                "isError": false
            })

            return true


        case "/network":

            currentPage = 1

            network.refresh()

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


    // =========================================================
    // CHAT SIGNALS
    // =========================================================

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


    // =========================================================
    // NETWORK SIGNALS
    // =========================================================

    Connections {
        target: network

        function onConnectionsReceived(connections) {

            networkConnections.clear()

            for (
                var i = 0;
                i < connections.length;
                i++
            ) {

                var connection = connections[i]

                networkConnections.append({
                    "protocol":
                        connection.protocol || "",

                    "local_ip":
                        connection.local_ip || "",

                    "local_port":
                        connection.local_port || 0,

                    "remote_ip":
                        connection.remote_ip || "",

                    "remote_port":
                        connection.remote_port || 0,

                    "status":
                        connection.status || "",

                    "pid":
                        connection.pid || 0,

                    "process_name":
                        connection.process_name || "Unknown",

                    "process_path":
                        connection.process_path || "",

                    "endpoint_scope":
                        connection.endpoint_scope || "",

                    "lifecycle":
                        connection.lifecycle || "",

                    "asn":
                        connection.asn || 0,

                    "organization":
                        connection.organization || "Unknown",

                    "isp":
                        connection.isp || "",

                    "domain":
                        connection.domain || "",

                    "enrichment_status":
                        connection.enrichment_status || "UNAVAILABLE",

                    "virustotal_url":
                        connection.virustotal_url || ""
                })
            }
        }


        function onRequestFailed(message) {

            console.log(
                "Network request failed:",
                message
            )
        }
    }


    // =========================================================
    // MAIN LAYOUT
    // =========================================================

    ColumnLayout {
        anchors.fill: parent

        spacing: 0


        // =====================================================
        // HEADER
        // =====================================================

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 52

            color: "#161b22"

            border.color: "#30363d"
            border.width: 1


            RowLayout {
                anchors.fill: parent

                anchors.leftMargin: 18
                anchors.rightMargin: 18

                spacing: 10


                Label {
                    text: "GHOST"

                    font.bold: true
                    font.pixelSize: 18

                    color: "#58a6ff"
                }


                Rectangle {
                    Layout.leftMargin: 16

                    width: 1
                    height: 24

                    color: "#30363d"
                }


                // -------------------------------------------------
                // TERMINAL BUTTON
                // -------------------------------------------------

                Button {
                    id: terminalButton

                    text: "Terminal"

                    flat: true

                    font.family: "Consolas"
                    font.bold: currentPage === 0

                    onClicked: {
                        currentPage = 0
                    }

                    contentItem: Text {
                        text: terminalButton.text

                        color:
                            currentPage === 0
                            ? "#58a6ff"
                            : "#8b949e"

                        font.family: "Consolas"
                        font.bold: currentPage === 0

                        horizontalAlignment:
                            Text.AlignHCenter

                        verticalAlignment:
                            Text.AlignVCenter
                    }

                    background: Rectangle {
                        color:
                            terminalButton.hovered
                            ? "#21262d"
                            : "transparent"

                        radius: 4
                    }
                }


                // -------------------------------------------------
                // NETWORK BUTTON
                // -------------------------------------------------

                Button {
                    id: networkButton

                    text:
                        "Network  "
                        + network.connectionCount

                    flat: true

                    font.family: "Consolas"
                    font.bold: currentPage === 1

                    onClicked: {

                        currentPage = 1

                        network.refresh()
                    }

                    contentItem: Text {
                        text: networkButton.text

                        color:
                            currentPage === 1
                            ? "#58a6ff"
                            : "#8b949e"

                        font.family: "Consolas"
                        font.bold: currentPage === 1

                        horizontalAlignment:
                            Text.AlignHCenter

                        verticalAlignment:
                            Text.AlignVCenter
                    }

                    background: Rectangle {
                        color:
                            networkButton.hovered
                            ? "#21262d"
                            : "transparent"

                        radius: 4
                    }
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

                    color:
                        chat.busy
                        ? "#f1c40f"
                        : "#3fb950"
                }


                Label {
                    text:
                        chat.busy
                        ? "Thinking..."
                        : "Idle"

                    color: "#8b949e"

                    font.family: "Consolas"
                }
            }
        }


        // =====================================================
        // MAIN PAGE AREA
        // =====================================================

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true

            currentIndex: currentPage


            // =================================================
            // TERMINAL PAGE
            // =================================================

            Item {

                ColumnLayout {
                    anchors.fill: parent

                    spacing: 0


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

                            boundsBehavior:
                                Flickable.StopAtBounds


                            delegate: TextArea {
                                width: terminal.width

                                text: model.text

                                readOnly: true
                                selectByMouse: true
                                persistentSelection: true

                                wrapMode:
                                    TextEdit.Wrap

                                font.family:
                                    "Consolas"

                                font.pixelSize: 15

                                color: {

                                    if (model.isError)
                                        return "#ff7b72"

                                    if (model.isCommand)
                                        return "#58a6ff"

                                    return "#e6edf3"
                                }

                                selectedTextColor:
                                    "#ffffff"

                                selectionColor:
                                    "#264f78"

                                background: null

                                padding: 0
                            }


                            ScrollBar.vertical:
                                ScrollBar {}
                        }
                    }


                    // -----------------------------------------
                    // INPUT
                    // -----------------------------------------

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

                                font.family:
                                    "Consolas"

                                font.pixelSize: 18

                                font.bold: true
                            }


                            TextArea {
                                id: commandInput

                                Layout.fillWidth: true
                                Layout.fillHeight: true

                                enabled:
                                    !chat.busy

                                placeholderText:
                                    "Ask Ghost anything..."

                                placeholderTextColor:
                                    "#6e7681"

                                color: "#e6edf3"

                                font.family:
                                    "Consolas"

                                font.pixelSize: 15

                                wrapMode:
                                    TextEdit.Wrap

                                selectByMouse: true

                                background: Rectangle {
                                    color: "transparent"
                                }


                                Keys.onReturnPressed:
                                    function(event) {

                                    if (
                                        !(
                                            event.modifiers
                                            & Qt.ShiftModifier
                                        )
                                    ) {

                                        submitCommand()

                                        event.accepted = true
                                    }
                                }


                                Component.onCompleted:
                                    forceActiveFocus()
                            }


                            Label {
                                text:
                                    chat.busy
                                    ? "RUNNING"
                                    : "READY"

                                color:
                                    chat.busy
                                    ? "#f1c40f"
                                    : "#3fb950"

                                font.family:
                                    "Consolas"

                                font.pixelSize: 13

                                font.bold: true
                            }
                        }
                    }
                }
            }


            // =================================================
            // NETWORK PAGE
            // =================================================

            Item {

                ColumnLayout {
                    anchors.fill: parent

                    spacing: 0


                    // -----------------------------------------
                    // NETWORK TITLE
                    // -----------------------------------------

                    Rectangle {
                        Layout.fillWidth: true

                        Layout.preferredHeight: 62

                        color: "#0d1117"


                        RowLayout {
                            anchors.fill: parent

                            anchors.leftMargin: 18
                            anchors.rightMargin: 18

                            spacing: 12


                            ColumnLayout {
                                spacing: 2


                                Label {
                                    text:
                                        "Network Activity"

                                    color: "#e6edf3"

                                    font.pixelSize: 19

                                    font.bold: true
                                }


                                Label {
                                    text:
                                        "Active public connections with ASN ownership"

                                    color: "#8b949e"

                                    font.family:
                                        "Consolas"

                                    font.pixelSize: 12
                                }
                            }


                            Item {
                                Layout.fillWidth: true
                            }


                            Label {
                                text:
                                    network.connectionCount
                                    + " active"

                                color: "#3fb950"

                                font.family:
                                    "Consolas"
                            }


                            Button {
                                id: refreshButton

                                text:
                                    network.busy
                                    ? "Refreshing..."
                                    : "Refresh"

                                enabled:
                                    !network.busy

                                onClicked: {
                                    network.refresh()
                                }


                                contentItem: Text {
                                    text:
                                        refreshButton.text

                                    color:
                                        "#e6edf3"

                                    font.family:
                                        "Consolas"

                                    horizontalAlignment:
                                        Text.AlignHCenter

                                    verticalAlignment:
                                        Text.AlignVCenter
                                }


                                background: Rectangle {

                                    color:
                                        refreshButton.hovered
                                        ? "#30363d"
                                        : "#21262d"

                                    border.color:
                                        "#30363d"

                                    radius: 5
                                }
                            }
                        }
                    }


                    // -----------------------------------------
                    // TABLE HEADER
                    // -----------------------------------------

                    Rectangle {
                        Layout.fillWidth: true

                        Layout.preferredHeight: 38

                        color: "#161b22"

                        border.color: "#30363d"
                        border.width: 1


                        RowLayout {
                            anchors.fill: parent

                            anchors.leftMargin: 18
                            anchors.rightMargin: 18

                            spacing: 12


                            Label {
                                Layout.preferredWidth: 175

                                text: "PROCESS"

                                color: "#8b949e"

                                font.family:
                                    "Consolas"

                                font.bold: true
                            }


                            Label {
                                Layout.preferredWidth: 60

                                text: "PID"

                                color: "#8b949e"

                                font.family:
                                    "Consolas"

                                font.bold: true
                            }


                            Label {
                                Layout.preferredWidth: 135

                                text: "REMOTE IP"

                                color: "#8b949e"

                                font.family:
                                    "Consolas"

                                font.bold: true
                            }


                            Label {
                                Layout.fillWidth: true

                                text: "OWNER"

                                color: "#8b949e"

                                font.family:
                                    "Consolas"

                                font.bold: true
                            }


                            Label {
                                Layout.preferredWidth: 80

                                text: "ASN"

                                color: "#8b949e"

                                font.family:
                                    "Consolas"

                                font.bold: true
                            }


                            Label {
                                Layout.preferredWidth: 65

                                text: "PORT"

                                color: "#8b949e"

                                font.family:
                                    "Consolas"

                                font.bold: true
                            }


                            Label {
                                Layout.preferredWidth: 105

                                text: "SECURITY"

                                color: "#8b949e"

                                font.family:
                                    "Consolas"

                                font.bold: true
                            }
                        }
                    }


                    // -----------------------------------------
                    // CONNECTION LIST
                    // -----------------------------------------

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        color: "#0d1117"


                        ListView {
                            id: networkList

                            anchors.fill: parent

                            clip: true

                            model: networkConnections

                            boundsBehavior:
                                Flickable.StopAtBounds


                            delegate: Rectangle {
                                width:
                                    networkList.width

                                height: 50

                                color:
                                    rowMouse.containsMouse
                                    ? "#161b22"
                                    : "#0d1117"

                                border.color:
                                    "#21262d"

                                border.width: 1


                                RowLayout {
                                    anchors.fill: parent

                                    anchors.leftMargin: 18
                                    anchors.rightMargin: 18

                                    spacing: 12


                                    // PROCESS
                                    Label {
                                        Layout.preferredWidth: 175

                                        text:
                                            model.process_name

                                        color: "#e6edf3"

                                        elide:
                                            Text.ElideRight

                                        font.family:
                                            "Consolas"

                                        ToolTip.visible:
                                            processMouse.containsMouse

                                        ToolTip.text:
                                            model.process_path


                                        MouseArea {
                                            id: processMouse

                                            anchors.fill: parent

                                            hoverEnabled: true

                                            acceptedButtons:
                                                Qt.NoButton
                                        }
                                    }


                                    // PID
                                    Label {
                                        Layout.preferredWidth: 60

                                        text:
                                            model.pid > 0
                                            ? model.pid
                                            : "-"

                                        color: "#8b949e"

                                        font.family:
                                            "Consolas"
                                    }


                                    // REMOTE IP
                                    TextArea {
                                        Layout.preferredWidth: 135

                                        Layout.alignment:
                                            Qt.AlignVCenter

                                        text:
                                            model.remote_ip

                                        readOnly: true
                                        selectByMouse: true
                                        persistentSelection: true

                                        wrapMode:
                                            TextEdit.NoWrap

                                        color: "#58a6ff"

                                        font.family:
                                            "Consolas"

                                        background: null

                                        padding: 0
                                    }


                                    // OWNER
                                    Label {
                                        Layout.fillWidth: true

                                        text:
                                            model.organization

                                        color: "#e6edf3"

                                        elide:
                                            Text.ElideRight

                                        font.family:
                                            "Consolas"

                                        ToolTip.visible:
                                            ownerMouse.containsMouse

                                        ToolTip.text:
                                            (
                                                model.isp !== ""
                                                ? model.isp
                                                : model.organization
                                            )
                                            +
                                            (
                                                model.domain !== ""
                                                ? "\n" + model.domain
                                                : ""
                                            )


                                        MouseArea {
                                            id: ownerMouse

                                            anchors.fill: parent

                                            hoverEnabled: true

                                            acceptedButtons:
                                                Qt.NoButton
                                        }
                                    }


                                    // ASN
                                    Label {
                                        Layout.preferredWidth: 80

                                        text:
                                            model.asn > 0
                                            ? "AS" + model.asn
                                            : "-"

                                        color: "#8b949e"

                                        font.family:
                                            "Consolas"
                                    }


                                    // PORT
                                    Label {
                                        Layout.preferredWidth: 65

                                        text:
                                            model.remote_port

                                        color: "#e6edf3"

                                        font.family:
                                            "Consolas"
                                    }


                                    // VIRUSTOTAL
                                    Button {
                                        id: virusTotalButton

                                        Layout.preferredWidth: 105

                                        text: "VirusTotal"

                                        enabled:
                                            model.virustotal_url !== ""

                                        onClicked: {

                                            network.openUrl(
                                                model.virustotal_url
                                            )
                                        }


                                        contentItem: Text {
                                            text:
                                                virusTotalButton.text

                                            color:
                                                virusTotalButton.enabled
                                                ? "#58a6ff"
                                                : "#6e7681"

                                            font.family:
                                                "Consolas"

                                            horizontalAlignment:
                                                Text.AlignHCenter

                                            verticalAlignment:
                                                Text.AlignVCenter
                                        }


                                        background: Rectangle {
                                            color:
                                                virusTotalButton.hovered
                                                ? "#21262d"
                                                : "transparent"

                                            border.color:
                                                "#30363d"

                                            border.width: 1

                                            radius: 4
                                        }
                                    }
                                }


                                MouseArea {
                                    id: rowMouse

                                    anchors.fill: parent

                                    hoverEnabled: true

                                    acceptedButtons:
                                        Qt.NoButton
                                }
                            }


                            ScrollBar.vertical:
                                ScrollBar {}
                        }


                        // -------------------------------------
                        // EMPTY STATE
                        // -------------------------------------

                        Label {
                            anchors.centerIn: parent

                            visible:
                                networkConnections.count
                                === 0
                                && !network.busy

                            text:
                                "No active public connections"

                            color: "#6e7681"

                            font.family:
                                "Consolas"
                        }


                        // -------------------------------------
                        // INITIAL LOADING
                        // -------------------------------------

                        BusyIndicator {
                            anchors.centerIn: parent

                            visible:
                                network.busy
                                && networkConnections.count
                                === 0

                            running: visible
                        }
                    }
                }
            }
        }


        // =====================================================
        // FOOTER
        // =====================================================

        Rectangle {
            Layout.fillWidth: true

            Layout.preferredHeight: 30

            color: "#0d1117"


            RowLayout {
                anchors.fill: parent

                anchors.leftMargin: 18
                anchors.rightMargin: 18


                Label {
                    text:
                        currentPage === 0
                        ? "Enter Send"
                        : "Auto-refresh 3s"

                    color: "#6e7681"

                    font.family:
                        "Consolas"

                    font.pixelSize: 12
                }


                Label {
                    visible:
                        currentPage === 0

                    text:
                        "Shift+Enter New Line"

                    color: "#6e7681"

                    font.family:
                        "Consolas"

                    font.pixelSize: 12
                }


                Item {
                    Layout.fillWidth: true
                }


                Label {
                    text:
                        currentPage === 0
                        ? "Mach 4 • AI Terminal"
                        : "Ghost • Network Monitor"

                    color: "#6e7681"

                    font.family:
                        "Consolas"

                    font.pixelSize: 12
                }
            }
        }
    }
}