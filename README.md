# GOK SmartBox for Home Assistant

Custom integration for GOK SmartBox tank-level devices (cloud polling).

## Installation (HACS)

1. HACS → Integrations → ⋮ → Custom repositories → add this repository, category **Integration**.
2. Install **GOK SmartBox** and restart Home Assistant.
3. Settings → Devices & Services → Add Integration → **GOK SmartBox**.

## Configuration

- **QR code string**: the full text of the QR code on the device (e.g. `AA11BB22CC33GOK-010`). The integration keeps only the leading 12 hex characters as the device ID.
- **Polling interval**: hourly or daily. Set it to the measuring interval configured on the device.

## Entities

Volume, fill level, battery, liquid height, last refill, last reading. Read-only; the device settings endpoint is not supported yet. See `specs/GOK_query.md`.
