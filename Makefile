.PHONY: run ui


run:
	@python -c "import makewaves; makewaves.main()"


ui:
	@bash scripts/makeui.sh


shortcut:
	@python scripts/create_shortcut.py
