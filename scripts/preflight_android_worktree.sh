#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: preflight_android_worktree.sh <primary-checkout> <worktree>" >&2
  exit 2
fi

primary_checkout="$1"
worktree="$2"
primary_local_properties="${primary_checkout}/local.properties"
worktree_local_properties="${worktree}/local.properties"

for directory in "$primary_checkout" "$worktree"; do
  if [[ ! -d "$directory" ]]; then
    echo "preflight failed: directory does not exist: ${directory}" >&2
    exit 2
  fi
done

if [[ ! -f "$primary_local_properties" ]]; then
  echo "preflight failed: trusted primary local.properties is missing" >&2
  exit 1
fi

if ! git -C "$worktree" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "preflight failed: target is not a git worktree" >&2
  exit 1
fi

initial_status="$(git -C "$worktree" status --porcelain=v1 --untracked-files=all --ignore-submodules=none)"
if [[ -n "$initial_status" ]]; then
  echo "preflight failed: target worktree already contains tracked or untracked changes" >&2
  echo "preflight failed: create a fresh worktree; do not hand off or copy a dirty checkout" >&2
  exit 1
fi

base_revision="$(git -C "$worktree" rev-parse HEAD)"

git_admin_dir="$(git -C "$worktree" rev-parse --absolute-git-dir)"
receipt_dir="${git_admin_dir}/codex-evidence"
receipt_path="${receipt_dir}/android-worktree-preflight.txt"

install -m 600 "$primary_local_properties" "$worktree_local_properties"

if ! git -C "$worktree" check-ignore -q local.properties; then
  echo "preflight failed: worktree local.properties is not ignored" >&2
  exit 1
fi

git -C "$worktree" submodule update --init --recursive

submodule_status="$(git -C "$worktree" submodule status --recursive)"
if [[ -n "$submodule_status" ]] && printf '%s\n' "$submodule_status" | awk 'substr($0,1,1)=="-" { found=1 } END { exit(found ? 0 : 1) }'; then
  echo "preflight failed: at least one recursive submodule is uninitialized" >&2
  exit 1
fi

final_status="$(git -C "$worktree" status --porcelain=v1 --untracked-files=all --ignore-submodules=none)"
if [[ -n "$final_status" ]]; then
  echo "preflight failed: worktree is dirty after local config and submodule initialization" >&2
  exit 1
fi

mkdir -p "$receipt_dir"
{
  echo "status=passed"
  echo "worktree=${worktree}"
  echo "base_revision=${base_revision}"
  echo "worktree_clean=true"
  echo "local_properties=present-and-ignored"
  echo "recursive_submodules=initialized"
} > "$receipt_path"

echo "status=passed"
echo "base_revision=${base_revision}"
echo "receipt=${receipt_path}"
