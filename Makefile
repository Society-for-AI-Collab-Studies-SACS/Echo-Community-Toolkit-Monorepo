.PHONY: g2v-sync-pull g2v-sync-push g2v-sync-verify

g2v-sync-pull:
	bash scripts/g2v_sync.sh --pull

g2v-sync-push:
	bash scripts/g2v_sync.sh --push

g2v-sync-verify:
	bash scripts/g2v_sync.sh --verify

