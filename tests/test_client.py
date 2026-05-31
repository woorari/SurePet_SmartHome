"""Tests for the SureHub client."""

from __future__ import annotations

import json
from typing import Any

import pytest

from surehub import AuthError, SureHubClient
from surehub.exceptions import AuthExpiredError

HOST = "app-api.production.surehub.io"


async def test_login_success(aresponses: Any) -> None:
    aresponses.add(
        HOST,
        "/api/auth/login",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=json.dumps({"data": {"token": "TOK123", "user": {"id": 1}}}),
        ),
    )
    client = SureHubClient()
    try:
        token = await client.login("you@example.com", "pw")
        assert token == "TOK123"
        assert client.token == "TOK123"
    finally:
        await client.close()


async def test_login_invalid_credentials(aresponses: Any) -> None:
    aresponses.add(
        HOST,
        "/api/auth/login",
        "POST",
        aresponses.Response(status=401, text="unauthorized"),
    )
    client = SureHubClient()
    try:
        with pytest.raises(AuthError):
            await client.login("you@example.com", "wrong")
    finally:
        await client.close()


async def test_get_account(aresponses: Any, me_start_data: dict[str, Any]) -> None:
    aresponses.add(
        HOST,
        "/api/me/start",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=json.dumps(me_start_data),
        ),
    )
    client = SureHubClient(token="TOK")
    try:
        account = await client.get_account()
        assert len(account.devices) == 4
        pet = account.pet(30001)
        assert pet is not None
        assert pet.name == "Whiskers"
    finally:
        await client.close()


async def test_expired_token_without_credentials_raises(aresponses: Any) -> None:
    aresponses.add(
        HOST,
        "/api/me/start",
        "GET",
        aresponses.Response(status=401, text="expired"),
    )
    client = SureHubClient(token="OLD")
    try:
        with pytest.raises(AuthExpiredError):
            await client.get_account()
    finally:
        await client.close()


async def test_silent_relogin_on_expiry(aresponses: Any, me_start_data: dict[str, Any]) -> None:
    # Token expired → client should silently re-login and retry.
    aresponses.add(HOST, "/api/me/start", "GET", aresponses.Response(status=401, text="expired"))
    aresponses.add(
        HOST,
        "/api/auth/login",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=json.dumps({"data": {"token": "NEWTOK"}}),
        ),
    )
    aresponses.add(
        HOST,
        "/api/me/start",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=json.dumps(me_start_data),
        ),
    )
    client = SureHubClient(token="OLD", email="you@example.com", password="pw")
    try:
        account = await client.get_account()
        assert client.token == "NEWTOK"
        assert len(account.devices) == 4
    finally:
        await client.close()


async def test_set_device_control(aresponses: Any) -> None:
    aresponses.add(
        HOST,
        "/api/device/20002/control/",
        "PUT",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=json.dumps({"data": {"locking": 2}}),
        ),
    )
    client = SureHubClient(token="TOK")
    try:
        result = await client.set_device_control(20002, {"locking": 2})
        assert result["data"]["locking"] == 2
    finally:
        await client.close()


async def test_set_pet_profile(aresponses: Any) -> None:
    aresponses.add(
        HOST,
        "/api/device/20002/tag/40001",
        "PUT",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=json.dumps({"data": {"profile": 3}}),
        ),
    )
    client = SureHubClient(token="TOK")
    try:
        result = await client.set_pet_profile(20002, 40001, 3)
        assert result["data"]["profile"] == 3
    finally:
        await client.close()


async def test_relogin_failure_raises_auth_error(aresponses: Any) -> None:
    # Stored password no longer valid → AuthError (HA maps this to reauth).
    aresponses.add(HOST, "/api/me/start", "GET", aresponses.Response(status=401))
    aresponses.add(HOST, "/api/auth/login", "POST", aresponses.Response(status=401))
    client = SureHubClient(token="OLD", email="you@example.com", password="bad")
    try:
        with pytest.raises(AuthError):
            await client.get_account()
    finally:
        await client.close()
