extends SceneTree

const ST_Dialogue_Box = preload("res://addons/dialogue_python_exporter/st_dialogue_box.gd")
const ST_Dialogue_Entry = preload("res://addons/dialogue_python_exporter/st_dialogue_entry.gd")
const ST_Dialogue_Style = preload("res://addons/dialogue_python_exporter/st_dialogue_style.gd")

func _init() -> void:
	print("[DialogueExporter] Started")

	var args := OS.get_cmdline_user_args()
	print("[DialogueExporter] User args: ", args)

	if args.size() < 2:
		printerr("[DialogueExporter] Missing args. Need: json_abs_path output_res_path")
		quit(1)
		return

	var json_path: String = args[0]
	var output_path: String = args[1]

	print("[DialogueExporter] JSON path: ", json_path)
	print("[DialogueExporter] Output path: ", output_path)

	var box := ST_Dialogue_Box.new()
	box.entries = []

	if not FileAccess.file_exists(json_path):
		printerr("[DialogueExporter] JSON file does not exist: ", json_path)
		quit(1)
		return

	var file := FileAccess.open(json_path, FileAccess.READ)

	if file == null:
		printerr("[DialogueExporter] Cannot open JSON file: ", json_path)
		quit(1)
		return

	var text := file.get_as_text()
	print("[DialogueExporter] JSON text length: ", text.length())

	var parsed = JSON.parse_string(text)

	if parsed == null:
		printerr("[DialogueExporter] JSON parse failed")
		quit(1)
		return

	if not parsed.has("entries"):
		printerr("[DialogueExporter] JSON has no entries")
		quit(1)
		return

	var entries: Array = parsed["entries"]
	print("[DialogueExporter] Entries count: ", entries.size())

	for i in entries.size():
		var data: Dictionary = entries[i]

		print("[DialogueExporter] Creating entry index: ", i)

		var style := ST_Dialogue_Style.new()
		style.text_color = _parse_color(data.get("text_color", "#ffffff"))
		style.text_speed = float(data.get("text_speed", 0.03))
		style.panel_moving = String(data.get("panel_moving", "None"))
		style.panel_style = String(data.get("panel_style", "Default"))

		var entry := ST_Dialogue_Entry.new()
		entry.speaker = String(data.get("speaker", "Player"))
		entry.content = String(data.get("content", ""))
		entry.seen_entry = bool(data.get("seen_entry", false))
		entry.style = style

		print("[DialogueExporter] Entry ",
			i,
			" speaker=", entry.speaker,
			" content_length=", entry.content.length(),
			" text_color=", style.text_color,
			" text_speed=", style.text_speed,
			" panel_moving=", style.panel_moving,
			" panel_style=", style.panel_style,
			" seen_entry=", entry.seen_entry
		)

		box.entries.append(entry)

	print("[DialogueExporter] Saving resource...")

	var err := ResourceSaver.save(box, output_path)

	if err != OK:
		printerr("[DialogueExporter] Resource save failed. Error code: ", err)
		quit(1)
		return

	print("[DialogueExporter] Resource saved successfully: ", output_path)
	quit(0)


func _parse_color(value: String) -> Color:
	if value.begins_with("#"):
		return Color.html(value)

	return Color(value)
