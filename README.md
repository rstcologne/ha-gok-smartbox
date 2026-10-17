# GOK SmartBox for Home Assistant

Custom integration for GOK SmartBox tank-level devices (cloud polling).

## Installation (HACS)

This integration is not in the HACS default store, so add it as a custom repository:

1. In Home Assistant, open **HACS** → **Integrations**.
2. Click the **⋮** menu (top right) → **Custom repositories**.
3. In the **Repository** field, paste:
   ```
   https://github.com/rstcologne/ha-gok-smartbox
   ```
4. Set **Category** to **Integration** and click **Add**.
5. Back in HACS, search for **GOK SmartBox**, open it and click **Download**.
6. Restart Home Assistant.
7. Go to **Settings** → **Devices & Services** → **Add Integration** and search for **GOK SmartBox**.

## Configuration

- **QR code string**: the full text of the QR code on the device (e.g. `AA11BB22CC33GOK-010`). The integration keeps only the leading 12 hex characters as the device ID.
- **Polling interval**: hourly or daily. Set it to the measuring interval configured on the device.

## Entities

Volume, fill level, battery, liquid height, last refill, last reading. Read-only; the device settings endpoint is not supported yet. See `specs/GOK_query.md`.
