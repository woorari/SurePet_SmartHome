# Emergency Unlock 🚨

> 🚧 Planned feature — not yet available in the current release.

A safety feature that **force-opens every cat/pet flap** during an emergency so
pets can get out, then restores the previous state afterward.

It clears, in one action, every mechanism that could keep a flap shut:

1. **Manual lock** → set to open.
2. **Curfew** → disabled so it doesn't re-lock on schedule.
3. **Per-pet "indoor only"** → every pet set to outdoor, so even indoor-only
   pets can pass.

## Intended usage

Tie it to a smoke / CO / security-alarm trigger:

```yaml
automation:
  - alias: "Cats escape on smoke alarm"
    triggers:
      - trigger: state
        entity_id: binary_sensor.smoke_detector
        to: "on"
    actions:
      - action: switch.turn_on
        target:
          entity_id: switch.all_flaps_emergency_unlock
  - alias: "Restore flaps when smoke clears"
    triggers:
      - trigger: state
        entity_id: binary_sensor.smoke_detector
        to: "off"
        for: "00:05:00"
    actions:
      - action: switch.turn_off
        target:
          entity_id: switch.all_flaps_emergency_unlock
```

## ⚠️ Safety limitation — please read

This feature is **cloud-dependent and not instant**. Every command is an
internet round-trip to the Sure Petcare cloud, and the change can take seconds
(occasionally longer) to reach the flap.

- **If your internet or the Sure Petcare cloud is down, it will not work.**
- It must **not** be your pets' only escape route in a fire.

Pair it with a local measure — a window left cracked, the flap's physical
unlock, or its fail-safe setting. Treat the integration's emergency unlock as a
best-effort assist, not a certified life-safety device.
