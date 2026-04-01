from __future__ import annotations

import os
import re
from hashlib import md5
from pathlib import Path
from typing import ClassVar, Dict, List

from autogen.code_utils import TIMEOUT_MSG
from autogen.coding import DockerCommandLineCodeExecutor
from autogen.coding.base import CodeBlock, CommandLineCodeResult
from autogen.coding.utils import _get_file_name_from_content, silence_pip


class DockerRCompatibleExecutor(DockerCommandLineCodeExecutor):
    """Project-local docker executor that adds native R block execution support."""

    DEFAULT_EXECUTION_POLICY: ClassVar[Dict[str, bool]] = {
        **DockerCommandLineCodeExecutor.DEFAULT_EXECUTION_POLICY,
        "r": True,
    }
    LANGUAGE_ALIASES: ClassVar[Dict[str, str]] = {
        **DockerCommandLineCodeExecutor.LANGUAGE_ALIASES,
        "rscript": "r",
    }
    WINDOWS_DESKTOP_NPIPE: ClassVar[str] = r"npipe:////./pipe/dockerDesktopLinuxEngine"

    def __init__(self, *args, **kwargs):
        # On Windows + Docker Desktop, docker SDK may default to docker_engine pipe,
        # which can fail with permission errors in this app process.
        if os.name == "nt" and not os.environ.get("DOCKER_HOST"):
            os.environ["DOCKER_HOST"] = self.WINDOWS_DESKTOP_NPIPE
        try:
            super().__init__(*args, **kwargs)
        except Exception as e:
            raise RuntimeError(
                "无法连接到 Docker Desktop。请确认 Docker Desktop 已启动，并在当前终端执行："
                "docker context use desktop-linux。"
                f" 当前 DOCKER_HOST={os.environ.get('DOCKER_HOST','<unset>')}。原始错误: {e}"
            ) from e

    @staticmethod
    def _cmd_for_lang(lang: str) -> str:
        if lang == "r":
            return "Rscript"
        if lang in {"bash", "sh", "python", "pwsh", "powershell", "ps1"}:
            return lang if lang != "powershell" else "pwsh"
        if lang == "shell":
            return "sh"
        if lang == "javascript":
            return "node"
        raise NotImplementedError(f"{lang} not recognized in code execution")

    @staticmethod
    def _patch_common_r_concat_errors(code: str) -> str:
        """
        Fix a frequent LLM mistake:
        txt <- "...", as.character(Sys.time()), "..."
        which is invalid R syntax and should be paste0(...).
        """
        pattern = re.compile(
            r'(?m)^(\s*\w+\s*<-\s*)"((?:[^"\\]|\\.)*)"\s*,\s*as\.character\((.*?)\)\s*,\s*"((?:[^"\\]|\\.)*)"\s*$'
        )
        return pattern.sub(r'\1paste0("\2", as.character(\3), "\4")', code)

    def execute_code_blocks(self, code_blocks: List[CodeBlock]) -> CommandLineCodeResult:
        if len(code_blocks) == 0:
            raise ValueError("No code blocks to execute.")

        outputs = []
        files = []
        last_exit_code = 0

        for code_block in code_blocks:
            lang = self.LANGUAGE_ALIASES.get(code_block.language.lower(), code_block.language.lower())
            if lang not in self.DEFAULT_EXECUTION_POLICY:
                outputs.append(f"Unsupported language {lang}\n")
                last_exit_code = 1
                break

            execute_code = self.execution_policies.get(lang, False)
            # Normalize all line endings to LF before write to avoid /bin/sh parse issues.
            code = code_block.code.replace("\r\n", "\n").replace("\r", "\n")
            if lang == "r":
                # Compatibility shim: some model outputs use exit(1), which is not an R base function.
                code = (
                    "exit <- function(code=0) quit(status=as.integer(code), save='no')\n"
                    + code
                )
                code = self._patch_common_r_concat_errors(code)
            code = silence_pip(code, lang)

            try:
                filename = _get_file_name_from_content(code, self._work_dir)
            except ValueError:
                outputs.append("Filename is not in the workspace")
                last_exit_code = 1
                break

            if not filename:
                filename = f"tmp_code_{md5(code.encode()).hexdigest()}.{lang}"

            code_path = Path(self._work_dir) / filename
            with code_path.open("w", encoding="utf-8", newline="\n") as fout:
                fout.write(code)
            files.append(code_path)

            if not execute_code:
                outputs.append(f"Code saved to {str(code_path)}\n")
                continue

            run_target = filename
            try:
                # When bind_dir != work_dir, files may be under /workspace/<subdir>/...
                run_target = code_path.resolve().relative_to(self._bind_dir.resolve()).as_posix()
            except Exception:
                run_target = filename

            command = ["timeout", str(self._timeout), self._cmd_for_lang(lang), run_target]
            result = self._container.exec_run(command)
            exit_code = result.exit_code
            output = result.output.decode("utf-8")
            if exit_code == 124:
                output += "\n" + TIMEOUT_MSG
            outputs.append(output)

            last_exit_code = exit_code
            if exit_code != 0:
                break

        code_file = str(files[0]) if files else None
        return CommandLineCodeResult(exit_code=last_exit_code, output="".join(outputs), code_file=code_file)
