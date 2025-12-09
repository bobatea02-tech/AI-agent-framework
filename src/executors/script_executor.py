# src/executors/script_executor.py
import subprocess
import sys
from typing import Dict, Any, Optional
from .base import BaseExecutor  # your BaseExecutor ABC

class ScriptExecutor(BaseExecutor):
    """
    Executes local Python scripts or shell commands.

    Supported modes (via config["mode"]):
    - "python_file": run a .py file with args
    - "python_inline": run inline Python code
    - "shell": run a shell command (careful: for trusted code only)
    """

    def execute(self, config: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        mode = config.get("mode", "python_file")

        if mode == "python_file":
            return self._run_python_file(config, inputs)
        elif mode == "python_inline":
            return self._run_python_inline(config, inputs)
        elif mode == "shell":
            return self._run_shell_command(config, inputs)
        else:
            raise ValueError(f"Unsupported script mode: {mode}")

    def _run_python_file(self, config: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a local Python script:
        config:
          path: path to .py file
          args_template: list of string args, may contain {placeholders}
        """
        path: str = config["path"]
        args_template = config.get("args_template", [])  # e.g. ["{value}", "--flag"]

        # Format arguments with inputs
        args = [arg.format(**inputs) for arg in args_template]

        # Build command: [python, script.py, arg1, arg2, ...]
        cmd = [sys.executable, path] + args

        # Run process safely (no shell=True)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=config.get("timeout", 60),
        )

        return {
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    def _run_python_inline(self, config: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run small inline Python snippets in a separate process.

        config:
          code: Python code string
        """
        code: str = config["code"]

        # You can inject inputs via env or simple format (trusted code only)
        formatted_code = code.format(**inputs)

        cmd = [sys.executable, "-c", formatted_code]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=config.get("timeout", 30),
        )

        return {
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    def _run_shell_command(self, config: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a shell command. Use only for trusted commands.

        config:
          command_template: e.g. "ls -la {path}"
        """
        # WARNING: This is NOT safe for untrusted input.
        command_template: str = config["command_template"]
        command = command_template.format(**inputs)

        # Because this is for internal trusted flows, shell=True is acceptable here,
        # but DO NOT expose user-controlled strings directly into this.
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=config.get("timeout", 30),
        )

        return {
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
