.PHONY: run ui shortcut build

run:
	@uv run makewaves

ui:
	@bash scripts/makeui.sh

build:
	@uv run pyinstaller scripts/makewaves-script.py \
	--onedir \
	--noconsole \
	--noconfirm \
	--name makewaves \
	--hidden-import makewaves \
	--paths ./makewaves \
	--add-data "makewaves/settings:makewaves/settings" \
	--add-data "makewaves/icons:makewaves/icons" \
	--icon makewaves/icons/makewaves_icon.ico

shortcut: build
	@uv run scripts/create_shortcut.py
