"""Thin HashiCorp Vault client wrapper used for database credential lookup."""

from __future__ import annotations

from typing import Any, Dict, Optional

import hvac


class VaultClient:
    """Configure and read secrets from a Vault server via ``hvac``."""

    def __init__(self, **kwargs: Any) -> None:
        """Store client constructor kwargs (url, token, etc.).

        Args:
            **kwargs: Passed to ``hvac.Client`` when ``setup`` is called.
        """
        self.vault_client: Optional[hvac.Client] = None
        self.vault_params: Dict[str, Any] = kwargs

    def setup(self) -> "VaultClient":
        """Instantiate the underlying ``hvac.Client`` and return ``self``.

        Returns:
            This client instance for fluent chaining.
        """
        self.vault_client = hvac.Client(**self.vault_params)
        return self

    def get_kv_v2(self, mount_point: str, path: str) -> Dict[str, Any]:
        """Read the latest KV v2 secret data at ``path``.

        Args:
            mount_point: KV v2 mount point name.
            path: Secret path within the mount.

        Returns:
            The ``data.data`` payload from Vault.

        Raises:
            RuntimeError: If ``setup`` has not been called.
        """
        if not self.vault_client:
            raise RuntimeError("Vault client is not initialized.")
        secret_version: dict = self.vault_client.secrets.kv.v2.read_secret_version(
            path=path,
            mount_point=mount_point,
        )
        return secret_version["data"]["data"]

    def read(self, path: str) -> Dict[str, Any]:
        """Read a generic Vault path (e.g. database credentials endpoint).

        Args:
            path: Full Vault API path to read.

        Returns:
            The secret ``data`` dict, or ``{}`` if Vault returns nothing.

        Raises:
            RuntimeError: If ``setup`` has not been called.
        """
        if not self.vault_client:
            raise RuntimeError("Vault client is not initialized.")
        secret: Dict[str, Any] = self.vault_client.read(path)
        return secret["data"] if secret else {}
