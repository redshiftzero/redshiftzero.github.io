default: build

.PHONY: dev
dev:  ## Run in dev mode
	hugo serve

.PHONY: build
build: ## Build the site
	hugo
	cp -r public/* .
	rm -R public/
	cp -r img/* static/img
	git add -u
	@printf "NOTE: Now inspect new files and stage them also if needed"

.PHONY: help
help: ## Print this message and exit
	@printf "redshiftzero.github.io"
	@printf "Subcommands:\n\n"
	@awk 'BEGIN {FS = ":.*?## "} /^[0-9a-zA-Z_-]+:.*?## / {printf "\033[36m%s\033[0m : %s\n", $$1, $$2}' $(MAKEFILE_LIST) \
		| sort \
		| column -s ':' -t
