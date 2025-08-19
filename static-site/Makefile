.PHONY: build serve dev clean help

# Default target
all: build

# Build the static site
build:
	@echo "🔨 Building static site..."
	python build.py
	@echo "✅ Build complete!"

# Serve the site locally
serve:
	@echo "🌐 Starting local server..."
	python serve.py

# Build and serve (development workflow)
dev: build serve

# Clean generated files
clean:
	@echo "🧹 Cleaning generated files..."
	rm -rf posts/ categories/ tags/
	@echo "✅ Clean complete!"

# Show help
help:
	@echo "Static Site Commands:"
	@echo "  make build  - Build the static site from Markdown"
	@echo "  make serve  - Serve the site locally at http://localhost:8000"
	@echo "  make dev    - Build and serve (development workflow)"
	@echo "  make clean  - Remove generated files"
	@echo "  make help   - Show this help message"
