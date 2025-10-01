import json
import os
import shutil
import subprocess
import sys
from typing import Optional

import requests

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, rely on system env vars


def _get_required_env(var_name: str, description: str) -> str:
    """Get a required environment variable or raise an error."""
    value = os.getenv(var_name)
    if not value:
        raise ValueError(
            f"Required environment variable '{var_name}' is not set.\n"
            f"This is needed for: {description}\n"
            f"Please add it to your .env file."
        )
    return value


# Azure DevOps Configuration - strict mode (no fallbacks)
AZURE_DEVOPS_RESOURCE = _get_required_env(
    "AZDO_RESOURCE_ID", 
    "Azure DevOps AAD resource ID"
)
API_VERSION = _get_required_env(
    "AZDO_API_VERSION",
    "Azure DevOps REST API version"
)
DEFAULT_ORGANIZATION = _get_required_env(
    "AZDO_ORG",
    "Azure DevOps organization name"
)
DEFAULT_PROJECT = _get_required_env(
    "AZDO_PROJECT",
    "Azure DevOps project name"
)


def get_az_access_token(resource: str = AZURE_DEVOPS_RESOURCE) -> str:
    """Obtain an AAD access token using Azure CLI. Requires `az login` first."""
    # Try to find az command
    az_cmd = shutil.which("az")
    if not az_cmd:
        # Try common Windows installation paths
        possible_paths = [
            r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd",
            r"C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd",
        ]
        for path in possible_paths:
            if shutil.which(path):
                az_cmd = path
                break
        
        if not az_cmd:
            raise RuntimeError("Azure CLI ('az') not found. Install Azure CLI and run 'az login'.")

    cmd = [az_cmd, "account", "get-access-token", "--resource", resource, "--output", "json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise RuntimeError(
            "Failed to get access token with Azure CLI. Ensure you ran 'az login'. "
            f"az error: {stderr}"
        ) from exc

    try:
        payload = json.loads(proc.stdout)
        token = payload.get("accessToken") or payload.get("access_token")
        if not token:
            raise KeyError("no access token in az output")
        return token
    except (json.JSONDecodeError, KeyError) as exc:
        raise RuntimeError("Unable to parse Azure CLI output for access token.") from exc


def list_fields(
    organization: str = DEFAULT_ORGANIZATION,
    project: str = DEFAULT_PROJECT,
    access_token: Optional[str] = None,
) -> dict:
    """
    Call Azure DevOps REST API to list fields visible in the specified project.
    Returns the parsed JSON response.

    Defaults to organization and project from environment variables.
    """
    if access_token is None:
        access_token = get_az_access_token()

    # Work item fields list endpoint (includes project scope)
    url = f"https://dev.azure.com/{organization}/{project}/_apis/wit/fields?api-version={API_VERSION}"
    headers = {"Accept": "application/json", "Authorization": f"Bearer {access_token}"}

    resp = requests.get(url, headers=headers, timeout=30)
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        body = resp.text
        raise RuntimeError(f"Request failed: {resp.status_code} {resp.reason}\n{body}") from exc

    return resp.json()


def _cli_main(argv):
    import argparse

    parser = argparse.ArgumentParser(
        description="List Azure DevOps fields for a project using az login (AAD token)."
    )
    parser.add_argument(
        "organization",
        nargs="?",
        default=DEFAULT_ORGANIZATION,
        help=f"Organization (default from AZDO_ORG env var)",
    )
    parser.add_argument(
        "project",
        nargs="?",
        default=DEFAULT_PROJECT,
        help=f"Project (default from AZDO_PROJECT env var)",
    )
    parser.add_argument("--token", help="Optional: pass access token directly (bypass az cli)")
    parser.add_argument("--raw", action="store_true", help="Print raw JSON without pretty formatting")
    args = parser.parse_args(argv)

    try:
        result = list_fields(args.organization, args.project, args.token)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    if args.raw:
        print(json.dumps(result))
    else:
        # Pretty print: show count and list of field names and reference names
        fields = result.get("value") if isinstance(result, dict) else None
        if isinstance(fields, list):
            print(f"Found {len(fields)} fields in {args.organization}/{args.project}")
            for f in fields:
                name = f.get("name") or "<no-name>"
                ref = f.get("referenceName") or "<no-ref>"
                print(f"- {name} ({ref})")
        else:
            print(json.dumps(result, indent=2))


if __name__ == "__main__":
    _cli_main(sys.argv[1:])