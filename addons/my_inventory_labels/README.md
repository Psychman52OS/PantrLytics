# My Inventory Labels — Home Assistant Add-on

This directory contains a Home Assistant Supervisor add-on for the `my_inventory_labels` Flask app.

Usage
- Commit this `addons/my_inventory_labels/` directory into your repository.
- In Home Assistant, add your repository URL under the Add-on Store → Repositories.
- Install the add-on and start it. Because the add-on uses Ingress, open the add-on's Web UI from Home Assistant.

Notes
- The add-on expects the Flask app to bind to `0.0.0.0` and to use port 5000 by default.
- If you prefer not to let Supervisor build the image, build and push the image to a registry (e.g. GHCR) and reference the `image` key in `config.json`.

Local testing

```bash
docker build -t my_inventory_labels:local .
docker run --rm -p 5000:5000 my_inventory_labels:local
# then visit http://localhost:5000
```
