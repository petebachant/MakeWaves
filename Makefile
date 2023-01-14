.PHONY: run ui


run:
	@python -c "import makewaves; makewaves.main()"


ui:
	@bash scripts/makeui.sh
