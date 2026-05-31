# Entities

The current release exposes **read-only** sensors. Controls (locking, curfew,
per-pet profiles, feeder settings) and the [[Emergency Unlock]] feature are on
the roadmap.

## Per device

| Entity | Type | Notes |
|--------|------|-------|
| Connectivity | binary_sensor | Whether the device is online |
| Battery | sensor | Percentage (battery-powered devices) |
| Battery voltage | sensor | Raw volts (diagnostic, disabled by default) |
| Signal strength | sensor | RSSI in dBm (diagnostic, disabled by default) |

## Cat / Pet Flap

| Entity | Type | Notes |
|--------|------|-------|
| Curfew | binary_sensor | Whether a curfew is currently active |

## Per pet

| Entity | Type | Notes |
|--------|------|-------|
| Inside | binary_sensor | Whether the pet is inside |
| Location | sensor | `inside` / `outside` |
| Location since | sensor | When the pet's location last changed |
| Last feeding | sensor | Timestamp of the last feeding |
| Last feeding amount | sensor | Grams consumed at the last feeding |
| Last drinking | sensor | Timestamp of the last drink |
| Last drinking amount | sensor | Amount consumed at the last drink |

Each pet also carries its photo as the entity picture, so it shows up in
dashboards and notifications.
