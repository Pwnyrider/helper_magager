# Helper Manager

A Home Assistant custom integration that exposes services for creating persistent helper entities programmatically — from automations, scripts, or blueprints — without needing to use the UI or restart HA.

## Installation

### Option 1: HACS (recommended)

1. In HACS, go to **Integrations → ⋮ → Custom repositories**.
2. Add `https://github.com/Pwnyrider/helper_magager` as category **Integration**.
3. Search for **Helper Manager** in HACS and click **Download**.
4. Restart Home Assistant.
5. Go to **Settings → Devices & Services → Add Integration** and search for **Helper Manager**.
6. Click through the one-step setup form (no options required).

### Option 2: Manual

1. Copy the `custom_components/helper_manager/` folder into your HA config's `custom_components/` directory.
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration** and search for **Helper Manager**.
4. Click through the one-step setup form (no options required).

## Reloading

After changing the integration files, use the **three-dot menu → Reload** on the Helper Manager card in Settings → Devices & Services, or call the `helper_manager.reload` action from Developer Tools.

## Services

All services are **idempotent**: if a helper with the same name already exists the call is silently skipped.

---

### `helper_manager.create_input_text`

Creates a persistent [input_text](https://www.home-assistant.io/integrations/input_text/) helper.

| Field | Required | Default | Description |
|---|---|---|---|
| `name` | ✅ | — | Friendly name |
| `initial` | | — | Initial text value |
| `min` | | `0` | Minimum character length |
| `max` | | `100` | Maximum character length |
| `pattern` | | — | Regex the value must match |
| `mode` | | `text` | `text` or `password` |
| `icon` | | — | MDI icon (e.g. `mdi:form-textbox`) |

---

### `helper_manager.create_input_boolean`

Creates a persistent [input_boolean](https://www.home-assistant.io/integrations/input_boolean/) (toggle) helper.

| Field | Required | Default | Description |
|---|---|---|---|
| `name` | ✅ | — | Friendly name |
| `initial` | | — | Initial state (`true`/`false`) |
| `icon` | | — | MDI icon |

---

### `helper_manager.create_input_number`

Creates a persistent [input_number](https://www.home-assistant.io/integrations/input_number/) (slider/box) helper.

| Field | Required | Default | Description |
|---|---|---|---|
| `name` | ✅ | — | Friendly name |
| `min` | ✅ | — | Minimum value |
| `max` | ✅ | — | Maximum value |
| `initial` | | — | Starting value |
| `step` | | `1` | Increment/decrement step |
| `mode` | | `slider` | `slider` or `box` |
| `unit_of_measurement` | | — | Unit label (e.g. `°C`) |
| `icon` | | — | MDI icon |

---

### `helper_manager.create_input_select`

Creates a persistent [input_select](https://www.home-assistant.io/integrations/input_select/) (dropdown) helper.

| Field | Required | Default | Description |
|---|---|---|---|
| `name` | ✅ | — | Friendly name |
| `options` | ✅ | — | List of selectable options |
| `initial` | | — | Initially selected option (must be in `options`) |
| `icon` | | — | MDI icon |

---

### `helper_manager.create_input_datetime`

Creates a persistent [input_datetime](https://www.home-assistant.io/integrations/input_datetime/) helper.

| Field | Required | Default | Description |
|---|---|---|---|
| `name` | ✅ | — | Friendly name |
| `has_date` | | `true` | Include a date component |
| `has_time` | | `true` | Include a time component |
| `initial` | | — | Initial value (`YYYY-MM-DD HH:MM:SS`, `YYYY-MM-DD`, or `HH:MM:SS`) |
| `icon` | | — | MDI icon |

## Example: create helpers from a script

```yaml
sequence:
  - action: helper_manager.create_input_boolean
    data:
      name: My Toggle
      icon: mdi:toggle-switch

  - action: helper_manager.create_input_number
    data:
      name: Target Temperature
      min: 10
      max: 30
      step: 0.5
      unit_of_measurement: "°C"
      icon: mdi:thermometer

  - action: helper_manager.create_input_select
    data:
      name: Operating Mode
      options:
        - "Eco"
        - "Normal"
        - "Boost"
      initial: "Normal"
```

## How it works

Home Assistant's built-in helper components (`input_boolean`, `input_number`, etc.) do not register HA services for creating helpers — they only expose WebSocket commands used by the UI. This integration bridges that gap by:

1. Checking whether the component registered a native `create` HA service (some HA versions do).
2. If not, locating the component's `StorageCollection` by introspecting the registered `{domain}/create` WebSocket handler, then calling `async_create_item()` directly — the same code path the UI uses.
