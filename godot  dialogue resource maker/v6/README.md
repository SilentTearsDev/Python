# Dialogue Python Editor v5 REAL

## Indítás

```bash
pip install PySide6
python dialogue_editor.py
```

## V5

Most már mindhárom ilyen:

- Speaker: dropdown + `+`
- Panel moving: dropdown + `+`
- Panel style: dropdown + `+`

A lenti külön speaker/panel listák ki lettek véve.

## Godot resource export

A `.json` mentés után automatikusan lefut a Godot headless exporter, ha ezek ki vannak töltve:

- Godot exe path
- Godot project root
- Resource output path

Alap output:

```text
res://dialogue_box_generated.tres
```

Az exporter bemásolja ezeket a projektedbe:

```text
res://addons/dialogue_python_exporter/json_to_resource_exporter.gd
res://addons/dialogue_python_exporter/st_dialogue_box.gd
res://addons/dialogue_python_exporter/st_dialogue_entry.gd
res://addons/dialogue_python_exporter/st_dialogue_style.gd
```

A resource classok:

- `ST_Dialogue_Box`
- `ST_Dialogue_Entry`
- `ST_Dialogue_Style`
