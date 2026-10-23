# Lampster (BLE robotlamp)

Custom integration in `custom_components/lampster/`. Stuurt een Lampster-lamp aan
via Bluetooth: licht (wit 2700–6500 K of RGB) en temperatuursensor. Werkt met elke
Bluetooth-adapter of ESPHome Bluetooth-proxy (`active: true`) in HA.

Installeren via HACS: ⋮ → Aangepaste repositories → `https://github.com/janjaaps/homeassistant-lampster`,
categorie *Integratie*. Herstart HA en voeg de lamp toe onder Instellingen → Apparaten & diensten.

Protocol (service `01ff5553-ba5e-f4ee-5ca1-eb1e5e4b1ce0`):

| Characteristic | Inhoud |
|---|---|
| `01ff5554` | status/commando: `C0` aan wit, `A0` aan RGB, `40` uit (was wit), `20` uit (was RGB) |
| `01ff5556` | wit: `[warm 0-100, koud 0-100]` |
| `01ff5559` | RGB: `[R, G, B]` 0-100 (helderheid inbegrepen) |
| `0x2A6E` | temperatuur (aanname: sint16 LE, 0,01 °C) |

Het uit-byte moet bij de huidige modus horen, anders flitst de lamp even aan.
Niet getest op echte hardware; verwacht kleine fouten.
