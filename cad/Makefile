.PHONY: help pcb-enclosure pcb-enclosure-slices pcb-enclosure-renders pcb-enclosure-show test

help:
	@echo "make pcb-enclosure          export base + lid + test slices (STL, print orientation)"
	@echo "make pcb-enclosure-slices   export only the test slices"
	@echo "make pcb-enclosure-renders  PNG renders + cross-sections into renders/"
	@echo "make pcb-enclosure-show     assembly in the OCP viewer (VS Code)"
	@echo "make test                   run the CAD tests"

pcb-enclosure:
	uv run python pcb_enclosure.py

pcb-enclosure-slices:
	uv run python pcb_enclosure.py --slices

pcb-enclosure-renders:
	uv run python render_pcb_enclosure.py renders

pcb-enclosure-show:
	uv run python pcb_enclosure.py --show

test:
	uv run pytest -q -p no:warnings
