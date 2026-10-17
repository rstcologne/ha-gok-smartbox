# GOK SmartBox Cloud API — Integration Spec

Reverse-engineered from the official Android app (`de.gok.smartbox`, v1.1,
build 11), a .NET MAUI app. This describes everything needed to query a
SmartBox tank-level device's cloud data for a third-party integration (e.g.
Home Assistant). No account/login is involved — authentication is a single
shared API key plus knowledge of the device's own identifier.

## 1. Base URL

```
https://smartboxazurefunction.azurewebsites.net/api/
```

This is a fixed Azure Functions app shared by all installs of the official
app. There is no per-user or per-region endpoint.

## 2. Authentication

Every request carries a single query parameter:

```
?code=<function-key>
```

- This is an **Azure Functions host/function key**, not a user credential.
  It is identical across all installations of the app (hard-coded in the
  app binary) and does not identify the caller.
- Current known value (extract and verify against your own app build if it
  ever rotates):
  ```
  slgep8fCk-LSQ1JvWIVP82lW_Xafx7g8b7j-5qqPrd3RAzFuo8uSOA==
  ```
- **There is no OAuth, bearer token, username/password, or session.** The
  only thing standing between "anyone" and a given device's data is
  knowledge of that device's identifier (see §3). Treat the identifier like
  a shared secret — an integration should not expose it beyond the local
  user's own config.

## 3. Device identifier ("mac")

The API key parameter for a specific device is its **MAC address, written as
12 uppercase hex characters with no separators** (no colons, no dashes), e.g.:

```
AA11BB22CC33
```

### Where to get it

1. **From the physical QR-code sticker on the device.** The sticker's QR
   code/printed text typically shows the MAC immediately followed by a
   product/model suffix, e.g.:
   ```
   AA11BB22CC33GOK-010
   ```
   The trailing part (`GOK-010` in this example — a model/product code) is
   **not** part of the device key and must be stripped. Take only the
   leading 12 hex characters.
2. **From the official app's own UI**, which displays it plainly as
   `Device-ID: AA11BB22CC33` on the device's detail screen — this is the
   authoritative, pre-stripped value and the easiest way to confirm you have
   the right string.

A simple heuristic for parsing a scanned/typed string: take the first 12
characters if they are valid hex (`[0-9A-Fa-f]{12}`); discard anything after
that.

```python
import re
m = re.match(r'^([0-9A-Fa-f]{12})', raw_qr_string)
mac = m.group(1).upper() if m else None
```

## 4. Endpoints

### 4.1 Get device data (read)

```
GET /api/sb/mac/<MAC>?code=<function-key>
```

- `<MAC>` — 12 hex chars, as above.
- Returns the device record plus its measurement history (observed response
  size: tens to ~100 KB depending on history retained server-side).
- No caching/ETag headers observed; poll at a sensible interval (the
  official app itself caches responses locally and only re-fetches when the
  cache is stale — a reasonable client-side cache window is on the order of
  minutes, not seconds, since the device itself typically reports roughly
  daily/hourly depending on its configured interval).

### 4.2 Update device settings (write)

```
PUT /api/ds/<MAC>?code=<function-key>
```

- Body: JSON, not fully reverse-engineered — corresponds to the editable
  fields on the app's "Device Settings" screen (tank shape, max height/volume,
  filling limit, name, language, measuring interval/unit — see §6). Treat
  this endpoint as **not yet fully specified**; don't rely on it for a v1
  integration without further traffic capture to confirm the exact payload
  shape.

Both endpoints sit behind the same `?code=` function key; no other headers
are required beyond standard `Content-Type: application/json` for the PUT.

## 5. Example request/response (anonymized)

```bash
curl "https://smartboxazurefunction.azurewebsites.net/api/sb/mac/AA11BB22CC33?code=<function-key>"
```

```json
{
  "key": "AA11BB22CC33",
  "measurements": [
    {
      "volume": 5290,
      "refillVolume": 3260,
      "battery": 40,
      "percent": 58,
      "height": 0.87,
      "onDemand": false,
      "timestamp": "2026-10-17T04:47:00.47Z"
    }
  ]
}
```

The `measurements` array is ordered oldest→newest in the samples observed;
the most recent reading is the last element.

## 6. Field reference

### Top level

| Field | Type | Notes |
|---|---|---|
| `key` | string | Device MAC, 12 hex chars, as sent in the request. |
| `measurements` | array | History of readings, oldest first. |
| `settings` | object | Device and tank configuration (see below). |

### `settings.tank`

| Field | Type | Notes |
|---|---|---|
| `setupDate` | string | ISO 8601, when the tank was configured. |
| `hvPairs` | array | Height/volume calibration pairs `[{"height": m, "volume": L}]`; the largest pair is the tank's total capacity. |
| `fillingLimit` | number | Configured maximum fill level, percent (e.g. `95`). Note: `max volume × fillingLimit` matches the constant `volume + refillVolume` seen in measurements. |
| `tankShape` | number | Index into the tank-shapes enum below (observed `0`). |
| `medium` | object | `{"type": <medium-type enum index>, "value": <density, kg/m³>}` (observed `{"type": 0, "value": 845}` ≈ heating oil). |

### `settings.device`

| Field | Type | Notes |
|---|---|---|
| `name` | string | Device name, default `SB_<MAC>`. |
| `unit` | number | Display-unit index (`0`=LITER, `1`=PERCENT, `2`=METER — inferred from enum order). |
| `interval` | number | Measuring-interval index (`0`=MINUTELY, `1`=HOURLY, `2`=DAILY, … — inferred from enum order). |
| `language` | number | Language index (observed `0`). |
| `timestamp` | string | ISO 8601, last settings change. |
| `mac` | string | Device MAC. |

Enum indices are inferred to map to the enum lists below in declaration order; verify against a device with non-default settings if you rely on them.

### Each `measurements[]` entry

| Field | Type | Unit / meaning |
|---|---|---|
| `volume` | number | Current tank content, **liters**. |
| `refillVolume` | number | Remaining volume that may still be added to fill the tank to its permissible maximum, liters ("zulässige Befüllmenge" in the official app). In observed data `volume + refillVolume` is constant (= max permissible capacity). |
| `battery` | number | Device battery level, **percent** (0–100). |
| `percent` | number | Fill level, **percent** of configured max capacity. |
| `height` | number | Measured liquid height, **meters**. |
| `onDemand` | bool | `true` if the reading was manually triggered (e.g. via the app's refresh/"Play" action), `false` if it was a scheduled/automatic reading. |
| `timestamp` | string | ISO 8601, UTC, with sub-second precision (e.g. `2026-10-17T04:47:00.4711785+00:00`). |

### Known enums (from app resources, relevant for settings/UI, not required for read-only polling)

- **Medium types** (what the tank holds): `HEATING_OIL`, `DIESEL`, `BIO_DIESEL`, `FAME`, `ADBLUE`, `NORMAL_GASOLINE`, `SUPER_GASOLINE`, `MOTOR_OIL`, `RAPESEED_OIL`, `PALM_OIL`, `WATER`.
- **Tank shapes**: `CYLINDER_LARGE`, `CYLINDER_SMALL`, `BALL`, `OVAL`, `CONCAVE`, `CONVEX`, `SHEET_STELL`, `CUSTOM_SHAPE`, `CUSTOM_DENSITY`.
- **Measuring/consumption intervals**: `MINUTELY`, `HOURLY`, `DAILY`, `WEEKLY`, `MONTHLY`.
- **Display units**: `LITER`, `PERCENT`, `METER`.

## 7. Practical integration notes

- **Polling cadence**: match the device's own reporting interval where
  possible (hourly/daily in the samples seen); hammering the endpoint more
  often than the device itself reports adds load without producing new data.
- **No push/webhook mechanism** was found — the app is pull-only (reads on
  app open / manual refresh / cached-expiry). A Home Assistant integration
  should poll on a `scan_interval`, not expect server push.
- **Multiple devices**: a user may have more than one SmartBox; each is
  queried independently by its own MAC under the same `?code=` key. The app
  stores a list of device keys locally (there's a `GetSbDevicesAsync`
  call backed by local storage, not a server "list my devices" endpoint) —
  so an integration must have the user supply each device's MAC explicitly
  (e.g. via its config flow), there is no "list all devices for this key"
  server call to rely on.
- **Error handling**: an unregistered/incorrect MAC returns `404 Not Found`
  with an empty body. No structured error payload was observed.
- **No TLS pinning** was found in the app, so standard HTTPS client
  behavior is sufficient.

## 8. Open items for further verification

- Exact JSON body shape expected by the `PUT /ds/<mac>` settings endpoint.
- Whether the function key is unique per app build/version or genuinely
  static long-term — re-verify if upgrading the reference app version.
- Rate limiting behavior server-side (none observed, not stress-tested).
