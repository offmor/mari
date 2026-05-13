# Changelog

## 2026-05-13

- **Breaking**: `mari_app_config_t` grew by 4 bytes — `has_net_id` field added between `magic` and `net_id`. Gateways provisioned with the previous firmware fall back to `MARI_NET_ID_DEFAULT` until re-provisioned with a `dotbot-provision` build that writes the new 12-byte prefix. (`559e5c2`)
