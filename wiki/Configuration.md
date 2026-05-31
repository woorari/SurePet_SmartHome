# Configuration

The integration is configured entirely through the Home Assistant UI.

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Surepet SmartHome**.
3. Enter the **email** and **password** for your Sure Petcare account.

That's it — your devices and pets are discovered automatically.

## Notes

- Your credentials are stored securely in Home Assistant's config entry storage
  and used only to keep your session alive. When the access token expires, the
  integration **re-logs-in automatically in the background** — you are not
  interrupted.
- The integration polls the Sure Petcare cloud roughly every few minutes.
- Devices appear grouped under your hub.

## Re-authentication

You'll only be asked to sign in again if your stored password stops working —
typically because you changed your Sure Petcare password. In that case Home
Assistant shows a **Re-authenticate** prompt; enter your current password to
reconnect.
