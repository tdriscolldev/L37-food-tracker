
# Install
install:
	uv sync --frozen
	cd client && yarn install

# Install for development (adds pre-commit hooks)
install-dev:
	$(MAKE) install
	uv run pre-commit install

# Format and lint
check:
	uv run pre-commit run --all-files

# Run front-end
run-ux:
	cd client && yarn run dev

# Run the backend server
run-server:
	uv run food-server

# Run items in parallel (Note: could instead have an inlined bash command here to exit all if either subprocess exits early)
run:
	$(MAKE) -j 2 run-ux run-server
