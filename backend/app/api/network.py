from typing import Optional

from fastapi import (
    APIRouter,
    Query,
)

from app.network.alert_engine import (
    alert_engine,
)

from app.network.service import (
    network_monitor,
)


router = APIRouter(
    prefix="/network",
    tags=["network"],
)


# ============================================================
# CONNECTIONS
# ============================================================

@router.get("/connections")
async def get_connections(
    scope: Optional[str] = Query(
        default=None,

        description=(
            "Filter by LOOPBACK, "
            "PRIVATE_LAN, or PUBLIC"
        ),
    ),

    lifecycle: Optional[str] = Query(
        default=None,

        description=(
            "Filter by ACTIVE, "
            "CLOSING, or CLOSED_STALE"
        ),
    ),
):

    connections = (
        network_monitor.get_connections()
    )

    if scope:

        normalized_scope = (
            scope.upper()
        )

        connections = [
            connection

            for connection
            in connections

            if (
                connection.endpoint_scope
                == normalized_scope
            )
        ]

    if lifecycle:

        normalized_lifecycle = (
            lifecycle.upper()
        )

        connections = [
            connection

            for connection
            in connections

            if (
                connection.lifecycle
                == normalized_lifecycle
            )
        ]

    return {
        "count":
            len(connections),

        "connections": [
            connection.to_dict()

            for connection
            in connections
        ],
    }


# ============================================================
# ALERTS
# ============================================================

@router.get("/alerts")
async def get_alerts():

    alerts = (
        alert_engine.pop_alerts()
    )

    return {
        "count":
            len(alerts),

        "alerts":
            alerts,
    }