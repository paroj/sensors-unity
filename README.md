# Sensors Unity

Allows monitoring the output of the `sensors` command graphically.

**Note:** for sensors-unity to work you have to manually give it the `hardware-observe` permission as:

```
sudo snap connect sensors-unity:hardware-observe :hardware-observe
```

## Configuration

Sensors Unity uses the `/etc/sensors3.conf` config file by default. However you can also specify a local override by copying it to `~/.config/sensors3.conf` (or `~/snap/sensors-unity/current/.config/sensors3.conf`).

This is useful in case you want to hide some unconnected sensors or give them more descriptive labels.

* to disable a sensor use the **ignore** statement
    ```sh
    # ignore everything from this chip
    chip "acpitz-virtual-0"
        ignore temp1
        ignore temp2
    ```
* to change the label use the **label** statement
    ```sh
    chip "coretemp-*"
        label temp1 "CPU Package"
    ```

## Translating

You can help [translating Sensors Unity to your language at POeditor](https://poeditor.com/join/project/k6KIME5b5H).