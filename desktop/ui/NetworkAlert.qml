import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

Window {
    id: alertWindow

    width: 430
    height: 210

    visible: false

    color: "transparent"

    modality: Qt.NonModal

    flags:
        Qt.Tool
        | Qt.FramelessWindowHint
        | Qt.WindowStaysOnTopHint
        | Qt.WindowDoesNotAcceptFocus


    property string alertTitle:
        "New outbound connection"

    property string processName:
        ""

    property string remoteIp:
        ""

    property int remotePort:
        0

    property string organization:
        ""

    property int asn:
        0

    property string severity:
        "NOTICE"

    property string virusTotalUrl:
        ""


    function positionWindow() {

        x =
            Screen.width
            - width
            - 24

        y = 24
    }


    function showAlert(alert) {

        alertTitle =
            alert.title
            || "New outbound connection"

        processName =
            alert.process_name
            || "Unknown process"

        remoteIp =
            alert.remote_ip
            || ""

        remotePort =
            alert.remote_port
            || 0

        organization =
            alert.organization
            || "Unknown owner"

        asn =
            alert.asn
            || 0

        severity =
            alert.severity
            || "NOTICE"

        virusTotalUrl =
            alert.virustotal_url
            || ""

        positionWindow()

        visible = true

        dismissTimer.restart()
    }


    Connections {
        target: network

        function onAlertReceived(alert) {

            alertWindow.showAlert(
                alert
            )
        }
    }


    Timer {
        id: dismissTimer

        interval: 8000

        repeat: false

        onTriggered: {

            alertWindow.visible = false
        }
    }


    Rectangle {
        anchors.fill: parent

        radius: 10

        color: "#161b22"

        border.width: 1

        border.color:
            severity === "WARNING"
            ? "#d29922"
            : "#58a6ff"


        ColumnLayout {
            anchors.fill: parent

            anchors.margins: 16

            spacing: 10


            RowLayout {
                Layout.fillWidth: true


                Rectangle {
                    width: 10
                    height: 10

                    radius: 5

                    color:
                        severity === "WARNING"
                        ? "#d29922"
                        : "#58a6ff"
                }


                Label {
                    text:
                        alertTitle

                    color: "#e6edf3"

                    font.pixelSize: 16

                    font.bold: true
                }


                Item {
                    Layout.fillWidth: true
                }


                Button {
                    id: closeButton

                    text: "×"

                    flat: true

                    onClicked: {

                        alertWindow.visible = false
                    }


                    contentItem: Text {
                        text:
                            closeButton.text

                        color: "#8b949e"

                        font.pixelSize: 20

                        horizontalAlignment:
                            Text.AlignHCenter

                        verticalAlignment:
                            Text.AlignVCenter
                    }


                    background: Rectangle {
                        color: "transparent"
                    }
                }
            }


            Label {
                Layout.fillWidth: true

                text:
                    processName

                color: "#ffffff"

                font.family: "Consolas"

                font.pixelSize: 15

                font.bold: true

                elide: Text.ElideRight
            }


            Label {
                Layout.fillWidth: true

                text:
                    remoteIp
                    +
                    (
                        remotePort > 0
                        ? ":" + remotePort
                        : ""
                    )

                color: "#58a6ff"

                font.family: "Consolas"

                font.pixelSize: 14
            }


            Label {
                Layout.fillWidth: true

                text:
                    organization
                    +
                    (
                        asn > 0
                        ? "  •  AS" + asn
                        : ""
                    )

                color: "#8b949e"

                font.family: "Consolas"

                font.pixelSize: 13

                elide: Text.ElideRight
            }


            Item {
                Layout.fillHeight: true
            }


            RowLayout {
                Layout.fillWidth: true


                Label {
                    text:
                        severity === "WARNING"
                        ? "Review recommended"
                        : "New network relationship"

                    color:
                        severity === "WARNING"
                        ? "#d29922"
                        : "#8b949e"

                    font.family: "Consolas"

                    font.pixelSize: 12
                }


                Item {
                    Layout.fillWidth: true
                }


                Button {
                    id: virusTotalButton

                    text:
                        "VirusTotal"

                    enabled:
                        virusTotalUrl !== ""

                    onClicked: {

                        network.openUrl(
                            virusTotalUrl
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
        }
    }
}