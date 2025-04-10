.PHONY: run ui shortcut build

run:
	@uv run makewaves

ui:
	@bash scripts/makeui.sh

build:
	@uv run pyinstaller makewaves/makewaves.py \
	--onedir \
	--noconsole \
	--name makewaves \
	--add-data "makewaves/settings:settings" \
	--add-data "makewaves/icons:icons" \
	--icon makewaves/icons/makewaves_icon.ico

shortcut:
	@uv run scripts/create_shortcut.py
