import os
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from langchain_ollama import ChatOllama
from ollama import Client

from quill.llm.errors import ProviderError
from quill.llm.provider import LLMProvider


def pull_model(model: str, host: str) -> None:
    try:
        client = Client(host=host)
        installed = {item.model for item in _get_client(client, host).list().models}
        if model in installed:
            from rich.console import Console
            Console().print(f"[green]Ollama model {model} is already available.[/green]")
            return
        from rich.console import Console
        from rich.progress import Progress, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn

        console = Console()
        console.print(f"Ollama model [bold]{model}[/bold] is missing; downloading it now.")
        with Progress(TextColumn("{task.description}"), BarColumn(), DownloadColumn(), TransferSpeedColumn(), console=console) as progress:
            task = progress.add_task(f"Pulling {model}", total=None)
            for state in _get_client(client, host).pull(model, stream=True):
                total, completed = getattr(state, "total", None), getattr(state, "completed", None)
                if total:
                    progress.update(task, total=total, completed=completed or 0)
        console.print(f"[green]Downloaded {model}.[/green]")
    except Exception as exc:
        raise ProviderError(f"Could not download Ollama model {model}: {exc}") from exc


def _get_client(client: Client, host: str) -> Client:
    try:
        client.list()
        return client
    except Exception as first_error:
        parsed = urlparse(host)
        if parsed.hostname not in {"localhost", "127.0.0.1", "::1"} or parsed.port not in {None, 11434}:
            raise ProviderError(f"Ollama is not reachable at {host}. Start the Ollama service and try again.") from first_error

        executable = shutil.which("ollama")
        if not executable and os.name == "nt":
            for candidate in (
                Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Programs" / "Ollama" / "ollama.exe",
                Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "Ollama" / "ollama.exe",
            ):
                if candidate.is_file():
                    executable = str(candidate)
                    break
        if not executable:
            executable = _install_ollama()

        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        try:
            subprocess.Popen(
                [executable, "serve"], stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=flags, start_new_session=os.name != "nt",
            )
        except OSError as exc:
            raise ProviderError(f"Could not start Ollama service: {exc}. Start Ollama manually and retry.") from exc
        for _ in range(20):
            time.sleep(0.5)
            try:
                client.list()
                return client
            except Exception:
                continue
        raise ProviderError("Ollama is installed but did not start. Open Ollama manually, then run `quill pull` again.") from first_error


def _install_ollama() -> str:
    if os.name != "nt":
        raise ProviderError(
            "Automatic Ollama installation is currently supported on Windows. Install Ollama from https://ollama.com/download, then retry."
        )

    from rich.console import Console
    from rich.progress import BarColumn, DownloadColumn, Progress, TextColumn, TransferSpeedColumn

    console = Console()
    installer_path: Path | None = None
    try:
        request = urllib.request.Request(
            "https://ollama.com/download/OllamaSetup.exe",
            headers={"User-Agent": "Quill installer"},
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            total = int(response.headers.get("Content-Length", "0")) or None
            with tempfile.NamedTemporaryFile(prefix="quill-ollama-", suffix=".exe", delete=False) as installer:
                installer_path = Path(installer.name)
                with Progress(TextColumn("{task.description}"), BarColumn(), DownloadColumn(), TransferSpeedColumn(), console=console) as progress:
                    task = progress.add_task("Downloading Ollama installer", total=total)
                    while chunk := response.read(1024 * 1024):
                        installer.write(chunk)
                        progress.update(task, advance=len(chunk))

        console.print("Verifying Ollama installer signature…")
        quoted_path = str(installer_path).replace("'", "''")
        verify_script = (
            f"$signature = Get-AuthenticodeSignature -LiteralPath '{quoted_path}'; "
            "if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Ollama Inc\\.') { exit 1 }"
        )
        verification = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", verify_script],
            capture_output=True, text=True, check=False,
        )
        if verification.returncode != 0:
            raise ProviderError("Ollama installer signature is invalid or the publisher could not be verified; the installer was not run.")

        console.print("Ollama installer is verified. Complete the installer window to continue.")
        result = subprocess.run([str(installer_path)], check=False)
        if result.returncode != 0:
            raise ProviderError(f"Ollama installer exited with code {result.returncode}.")

        executable = shutil.which("ollama")
        candidates = (
            Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Programs" / "Ollama" / "ollama.exe",
            Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "Ollama" / "ollama.exe",
        )
        if not executable:
            executable = next((str(path) for path in candidates if path.is_file()), None)
        if not executable:
            raise ProviderError("Ollama installer finished, but the executable was not found. Restart your terminal and retry.")
        return executable
    except ProviderError:
        raise
    except Exception as exc:
        raise ProviderError(f"Could not download or install Ollama from its official website: {exc}") from exc
    finally:
        if installer_path:
            installer_path.unlink(missing_ok=True)


class OllamaProvider(LLMProvider):
    def __init__(self, model: str, host: str) -> None:
        self.model = model
        self.host = host

    def generate(self, prompt: str) -> str:
        try:
            pull_model(self.model, self.host)
            response = ChatOllama(model=self.model, base_url=self.host, temperature=0.2).invoke(prompt)
            content = response.content
            if not isinstance(content, str) or not content.strip():
                raise ProviderError("Ollama returned an empty response.")
            return content
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"Ollama ({self.model}) is unavailable: {exc}") from exc
