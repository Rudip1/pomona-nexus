# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Adapted from cogni-nav-x0 / vf_robot_bringup (Apache-2.0, same author).
# =============================================================================
# pomona_navigation / launch_utils / compose_params.py
# =============================================================================
# Composes a final Nav2 params YAML at launch time by deep-merging:
#
#     nav2_base.yaml                     ← controller-agnostic Nav2 skeleton
#   ⊕ controllers/<controller>.yaml     ← FollowPath: block (mppi | dwb)
#   ⊕ planners/<planner>.yaml           ← GridBased: block (NavFn)
#   ⊕ localization/amcl.yaml            ← amcl: block (only when localization=amcl)
#   ⊕ robot rewrites                    ← footprint, frames, velocity limits
#
# The merged file is written to /tmp/ and its path is returned; the launch
# file passes that single path to every Nav2 node.
#
# Strict mode (default): a robot-profile rewrite whose dotted key does not
# already exist in the merged params raises a clear "did you mean ...?" error
# at launch — catching typos instead of silently mis-configuring a node.
# =============================================================================

from __future__ import annotations

import difflib
import os
import sys
import tempfile
from typing import Any

import yaml


class ComposeError(RuntimeError):
    """Raised when composition fails for a user-fixable reason."""


def _load_yaml(path: str) -> dict:
    """Load a YAML file. Returns {} for empty files. Raises on parse errors."""
    if not os.path.isfile(path):
        raise ComposeError(f"YAML file not found: {path}")
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ComposeError(f"Failed to parse YAML file '{path}':\n  {e}")
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ComposeError(
            f"YAML file '{path}' must contain a top-level dict, "
            f"got {type(data).__name__}"
        )
    return data


def _deep_merge(base: dict, overlay: dict) -> dict:
    """Recursively merge `overlay` into `base` (overlay wins; lists replaced)."""
    out = dict(base)
    for key, ov_val in overlay.items():
        if key in out and isinstance(out[key], dict) and isinstance(ov_val, dict):
            out[key] = _deep_merge(out[key], ov_val)
        else:
            out[key] = ov_val
    return out


def _set_path(d: dict, dotted_path: str, value: Any, *, strict: bool) -> None:
    """Set d[a][b][c] = value for "a.b.c"; strict mode requires keys to exist."""
    parts = dotted_path.split(".")
    if not parts or any(p == "" for p in parts):
        raise ComposeError(f"Invalid rewrite path: '{dotted_path}'")

    cursor: Any = d
    walked: list[str] = []
    for part in parts[:-1]:
        walked.append(part)
        if not isinstance(cursor, dict):
            raise ComposeError(
                f"Rewrite path '{dotted_path}' descends into non-dict at "
                f"'{'.'.join(walked[:-1])}' (value is {type(cursor).__name__})"
            )
        if part not in cursor:
            if strict:
                _raise_unknown_key(dotted_path, walked, cursor)
            cursor[part] = {}
        cursor = cursor[part]

    if not isinstance(cursor, dict):
        raise ComposeError(
            f"Rewrite path '{dotted_path}' parent is not a dict "
            f"(parent path: '{'.'.join(walked)}')"
        )
    last = parts[-1]
    if strict and last not in cursor:
        walked.append(last)
        _raise_unknown_key(dotted_path, walked, cursor)
    cursor[last] = value


def _raise_unknown_key(full_path: str, walked: list[str], parent_dict: dict) -> None:
    """Raise ComposeError naming the missing key, with close-match suggestions."""
    missing = walked[-1]
    siblings = [k for k in parent_dict.keys() if isinstance(k, str)]
    suggestions = difflib.get_close_matches(missing, siblings, n=3, cutoff=0.6)
    where = ".".join(walked[:-1]) or "<root>"
    msg = [
        f"Robot profile rewrites '{full_path}' but segment '{missing}' does not "
        f"exist under '{where}' in the merged Nav2 params.",
    ]
    if suggestions:
        msg.append(f"  Did you mean: {', '.join(suggestions)}?")
    if siblings:
        shown = sorted(siblings)[:8]
        more = "" if len(siblings) <= 8 else f" (and {len(siblings) - 8} more)"
        msg.append(f"  Available keys at '{where}': {', '.join(shown)}{more}")
    msg.append(
        "  Fix: correct the key in the robot profile YAML, "
        "or set strict=False to add a new key intentionally."
    )
    raise ComposeError("\n".join(msg))


def load_robot_profile(path: str, controller_family: str | None = None) -> dict[str, Any]:
    """Load a robot profile YAML → flat {dotted.key: value} rewrite dict.

    Applies `rewrites:` (always) then `controller_overrides[controller_family]`
    (if given). Controller-family overrides exist because each controller plugin
    names the same physical concept differently (mppi vx_max vs dwb max_vel_x),
    so listing all of them in the always-applied block would fail strict mode.
    """
    data = _load_yaml(path)
    if "rewrites" not in data:
        raise ComposeError(
            f"Robot profile '{path}' is missing the 'rewrites:' section."
        )
    rewrites = dict(data["rewrites"])
    if not isinstance(rewrites, dict):
        raise ComposeError(
            f"Robot profile '{path}' 'rewrites:' is not a dict "
            f"(got {type(rewrites).__name__})"
        )
    if controller_family is not None:
        root = data.get("controller_overrides", {}) or {}
        overrides = root.get(controller_family, {}) or {}
        if not isinstance(overrides, dict):
            raise ComposeError(
                f"controller_overrides.{controller_family} is not a dict"
            )
        for k, v in overrides.items():
            rewrites[k] = v
    for k in rewrites:
        if not isinstance(k, str) or "." not in k:
            raise ComposeError(
                f"Robot profile '{path}' has invalid rewrite key '{k}'. "
                f"Keys must be dotted paths."
            )
    return rewrites


def compose(
    base_path: str,
    controller_path: str,
    planner_path: str | None,
    localization_path: str | None,
    robot_rewrites: dict[str, Any],
    *,
    label: str = "composed",
    strict: bool = True,
    debug: bool = False,
) -> str:
    """Compose a final Nav2 params YAML and return its /tmp path."""
    merged = _deep_merge(_load_yaml(base_path), _load_yaml(controller_path))
    if planner_path is not None:
        merged = _deep_merge(merged, _load_yaml(planner_path))
    if localization_path is not None:
        merged = _deep_merge(merged, _load_yaml(localization_path))
    for dotted_key, value in robot_rewrites.items():
        _set_path(merged, dotted_key, value, strict=strict)

    safe_label = "".join(c if c.isalnum() or c in "_-" else "_" for c in label)
    fd, out_path = tempfile.mkstemp(
        prefix=f"nav2_{safe_label}_", suffix=".yaml",
        dir=tempfile.gettempdir(), text=True,
    )
    with os.fdopen(fd, "w") as f:
        f.write(
            "# AUTO-GENERATED by pomona_navigation/launch_utils/compose_params.py\n"
            "# Overwritten on every launch — do not edit.\n"
            f"#   base:         {base_path}\n"
            f"#   controller:   {controller_path}\n"
            f"#   planner:      {planner_path or '(base default)'}\n"
            f"#   localization: {localization_path or '(none)'}\n"
            f"#   robot:        {len(robot_rewrites)} rewrites\n#\n"
        )
        yaml.safe_dump(merged, f, default_flow_style=False, sort_keys=False)
    if debug:
        print(f"[compose_params] wrote {out_path}", file=sys.stderr)
    return out_path
