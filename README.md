# Sure Petcare for Home Assistant

A custom [Home Assistant](https://www.home-assistant.io/) integration for
**Sure Petcare** (SureHub) connected pet devices — cat/pet flaps, feeders, water
stations and the hub — with a focus on **full device coverage** and
**automation-friendly** features the built-in integration doesn't offer.

> **Unofficial & unaffiliated.** This project is not affiliated with, endorsed
> by, or supported by Sure Petcare / SureHub. It talks to the same cloud API the
> official apps use. The API is undocumented and may change at any time.

---

## Status

🚧 **Early development.** The integration is being built and is not yet ready
for production use. User documentation lives in the [project wiki](../../wiki).

---

## Why another integration?

The built-in Home Assistant integration covers presence, locks and battery, but
leaves a lot on the table. This project aims to expose the **complete** device
range and turn the data into things you can actually automate around:

- Feeder food weight & consumption, water-station drinking data
- Curfew as editable schedule entities, full lock-mode control
- Per-pet indoor/outdoor permissions
- Long-term statistics (food eaten, water drunk, time outside)
- First-class **events & device triggers** with **rich, actionable
  notifications** (including your pet's photo)
- An **Emergency Unlock** safety feature (see below)

See the **[project wiki](../../wiki)** for the full feature catalog and guides.

---

## Supported devices

| Device | Support |
|--------|---------|
| Hub | ✅ |
| Cat Flap Connect | ✅ |
| Pet Flap Connect | ✅ |
| Feeder Connect | ✅ |
| Feeder Lite | ✅ |
| Felaqua Connect (water station) | ✅ |
| Repeater | ✅ (signal/diagnostics) |
| Programmer | ✅ (signal/diagnostics) |

---

## Emergency Unlock 🚨

A safety feature that **force-opens every flap** during an emergency — clearing
manual locks, curfew, and per-pet indoor-only restrictions in one action — so
pets can get out. Designed to be tied to a smoke / CO / security-alarm trigger,
with the previous state restored automatically afterward.

> ⚠️ **This is cloud-dependent and not instant.** If your internet or the
> SureHub cloud is down, it will not fire. Treat it as a best-effort assist, not
> your pets' only escape route in a fire. Pair it with a local measure (a
> cracked window, the flap's physical unlock or fail-safe setting).

---

## Installation

> Installation details will be finalized when the first release is published.

Planned: install via [HACS](https://hacs.xyz/) as a custom repository, then add
the integration from **Settings → Devices & Services**.

## Configuration

The integration is configured entirely through the UI (config flow):

1. **Settings → Devices & Services → Add Integration → Sure Petcare**
2. Enter your Sure Petcare **email** and **password**.

Your credentials are stored securely by Home Assistant and used to keep the
connection alive automatically — you won't be asked to sign in again unless you
change your Sure Petcare password.

---

## Documentation

User documentation — installation, configuration, supported entities, the
Emergency Unlock guide and FAQ — lives in the **[project wiki](../../wiki)**.

---

## Disclaimer

This is a hobby project provided "as is", without warranty of any kind. It
relies on an undocumented cloud API; functionality may break if that API
changes. Use at your own risk, and never rely on it as a sole safety mechanism
for your pets.

## Contributing

Issues and pull requests are welcome. Please open an issue to discuss
significant changes before submitting a PR.

## Credits & acknowledgements

This project stands on the shoulders of the wider Sure Petcare community. Huge
thanks to:

- **[Sure Petcare / SureHub](https://www.surepetcare.com/)** — for the devices
  and the cloud service this integration talks to.
- **[benleb/surepy](https://github.com/benleb/surepy)** &
  **[benleb/sureha](https://github.com/benleb/sureha)** — the original Python
  client and Home Assistant work that mapped much of the API.
- **[Home Assistant core `surepetcare`](https://www.home-assistant.io/integrations/surepetcare/)**
  — the built-in integration and its contributors.
- **[FredrikM97/py-surepetcare](https://github.com/FredrikM97/py-surepetcare)**
  & **[FredrikM97/hass-surepetcare](https://github.com/FredrikM97/hass-surepetcare)**
  — a modern client and integration whose design patterns informed this one.
- **[Sickboy78/ioBroker.sureflap](https://github.com/Sickboy78/ioBroker.sureflap)**
  — a feature-complete ioBroker adapter and an excellent behavioural reference.
- **[fabieu/surehub-api](https://github.com/fabieu/surehub-api)** — additional
  API documentation.

## License

Released under the [MIT License](LICENSE).
