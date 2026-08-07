from __future__ import annotations

import os
import sys

from ls_updater_cli import Colors, print_c


def _build_jobs(csv_paths, ls_paths):
    jobs = []
    for csv_path in csv_paths:
        for ls_path in ls_paths:
            jobs.append((csv_path, ls_path))
    return jobs


def prepare_run_context(
    args,
    resolve_paths,
    detect_env_from_csv,
    detect_env_from_ls,
    collect_env_options_from_ls,
    normalize_env_option,
    get_env_info,
    prompt_env_from_list,
    prompt_env_conflict,
    prompt_confirm_action,
    prompt_precision_override,
    prompt_int_lock_mode,
    print_confirm_banner,
    preview_csv_info,
    sync_parse_runtime,
    clear_preview_state,
):
    while True:
        csv_paths, ls_paths, restart = resolve_paths(args)
        if restart:
            clear_preview_state()
            continue

        csv_envs = {path: detect_env_from_csv(path) for path in csv_paths}
        ls_envs = {path: detect_env_from_ls(path) for path in ls_paths}
        env_options = collect_env_options_from_ls(ls_paths)
        explicit_env_name = None
        if args.env:
            env_arg = str(args.env).upper()
            if env_arg == "ALL":
                explicit_env_name = "ALL"
            else:
                normalized_env = normalize_env_option(env_arg)
                explicit_env_name = normalized_env.get("name") if normalized_env else env_arg
            for csv_path in csv_paths:
                csv_info = get_env_info(csv_envs, csv_path)
                csv_info["env"] = explicit_env_name
                csv_info["source"] = "arg"
                csv_envs[csv_path] = csv_info

        if env_options:
            for csv_path in csv_paths:
                csv_info = get_env_info(csv_envs, csv_path)
                if not csv_info.get("env"):
                    ls_env_set = {info.get("env") for info in ls_envs.values() if info.get("env")}
                    if len(ls_env_set) == 1 and not args.env:
                        csv_info["env"] = ls_env_set.pop()
                        csv_info["source"] = "ls_fallback"
                    else:
                        label = os.path.basename(csv_path)
                        csv_info["env"] = prompt_env_from_list(
                            label,
                            env_options,
                            show_label=(len(csv_paths) > 1),
                            include_all=(len(csv_paths) == 1),
                            override_label=False,
                        )
                    csv_envs[csv_path] = csv_info

        decision_cache = {}
        if not args.silent and not args.env:
            for csv_path in csv_paths:
                csv_env = csv_envs.get(csv_path, {}).get("env")
                if not csv_env:
                    continue
                for ls_path in ls_paths:
                    ls_env = ls_envs.get(ls_path, {}).get("env")
                    if not ls_env or csv_env == ls_env:
                        continue
                    cache_key = (csv_env, ls_env)
                    if cache_key not in decision_cache:
                        choice = prompt_env_conflict(csv_env, ls_env, csv_path, ls_path, env_options)
                        if choice == "override":
                            override_env = prompt_env_from_list(
                                "Override temperature",
                                env_options,
                                show_label=True,
                                include_all=False,
                                override_label=False,
                            )
                            decision_cache[cache_key] = ("override", override_env)
                        else:
                            decision_cache[cache_key] = choice

        if not args.silent:
            prompt_precision_override()
            prompt_int_lock_mode()
            sync_parse_runtime()
            while True:
                print_confirm_banner(csv_paths, ls_paths, csv_envs)
                choice = prompt_confirm_action()
                if choice == "restart":
                    clear_preview_state()
                    restart = True
                    break
                if choice == "override_env":
                    if not env_options:
                        print_c("No temperature options detected from LS files.", Colors.WARNING)
                        continue
                    for csv_path in csv_paths:
                        info = get_env_info(csv_envs, csv_path)
                        new_env = prompt_env_from_list(
                            os.path.basename(csv_path),
                            env_options,
                            highlight_label=False,
                            show_label=(len(csv_paths) > 1),
                            include_all=(len(csv_paths) == 1),
                        )
                        info["env"] = new_env
                        info["source"] = "override"
                        csv_envs[csv_path] = info
                    continue
                if choice == "override_columns":
                    for csv_path in csv_paths:
                        preview_csv_info(csv_path, args, force_prompt=True, display=True)
                    continue
                if choice == "quit":
                    sys.exit("User quit.")
                break
            if restart:
                continue
        break

    any_q_ls = any((info.get("env") or "").startswith("Q") for info in ls_envs.values())
    jobs = _build_jobs(csv_paths, ls_paths)
    return {
        "csv_paths": csv_paths,
        "ls_paths": ls_paths,
        "csv_envs": csv_envs,
        "ls_envs": ls_envs,
        "env_options": env_options,
        "decision_cache": decision_cache,
        "any_q_ls": any_q_ls,
        "jobs": jobs,
    }


__all__ = ["prepare_run_context"]