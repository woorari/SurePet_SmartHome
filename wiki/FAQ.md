# FAQ

### Is this official?

No. It's an unofficial, community integration and is not affiliated with or
endorsed by Sure Petcare. It uses the same cloud API as the official apps.

### Does it work offline / locally?

No. It talks to the Sure Petcare cloud, so it needs an internet connection and a
working hub.

### Is my password stored?

Yes — securely, in Home Assistant's config entry storage, and only so the
integration can re-login for you automatically when the access token expires.
You won't be prompted to sign in again unless your stored password stops working
(for example, because you changed your Sure Petcare password).

### How often does it update?

It polls the cloud every few minutes. Sure Petcare devices themselves only
report to the cloud periodically, so near-real-time updates aren't possible.

### Why is the built-in `surepetcare` integration not enough for me?

The built-in one covers presence, locks and battery. This project aims to add
feeder/water consumption, curfew and per-pet controls, statistics, richer
automations and the [[Emergency Unlock]] safety feature.

### A device shows as unavailable

Check that the device is online in the official Sure Petcare app, that your hub
has power and network, and that re-authentication isn't pending in Home
Assistant.

### How do I report a bug or request a feature?

Open an issue on the GitHub repository.
