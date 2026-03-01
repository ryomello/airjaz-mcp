#!/usr/bin/env python3
import os
import httpx
from fastmcp import FastMCP

mcp = FastMCP("AirJaz")

AIRJAZ_URL    = os.environ.get("AIRJAZ_URL",    "https://airjaz.vercel.app/api/intake")
AIRJAZ_SECRET = os.environ.get("AIRJAZ_SECRET", "")


def _headers():
    return {
        "Authorization": f"Bearer {AIRJAZ_SECRET}",
        "Content-Type": "application/json",
    }


@mcp.tool(description=(
    "Add an artist to the AirJaz A&R scouting tracker. "
    "Use this whenever the user wants to log a new artist for review, "
    "or when an email recommends an artist worth checking out. "
    "handle is required (Instagram/TikTok username, without @). "
    "source: email=email tip, irl=mentioned in chat, tiktok=TikTok, spotify=Spotify. "
    "link is optional profile URL. note is optional context. score is 1-5 (default 3)."
))
def add_artist(handle: str, source: str = "irl", link: str = "", note: str = "", score: int = 3) -> dict:
    payload = {"handle": handle.lstrip("@").strip(), "source": source, "score": max(1, min(5, score))}
    if link: payload["link"] = link
    if note: payload["bio"] = note
    try:
        r = httpx.post(AIRJAZ_URL, json=payload, headers=_headers(), timeout=10)
        if r.status_code == 201:
            return {"ok": True, "message": f"Added {handle} to AirJaz (id: {r.json().get('id','?')})"}
        elif r.status_code == 409:
            return {"ok": False, "message": f"{handle} is already in AirJaz"}
        elif r.status_code == 401:
            return {"ok": False, "message": "Auth error - check AIRJAZ_SECRET on Render"}
        else:
            return {"ok": False, "message": f"AirJaz returned {r.status_code}: {r.text}"}
    except Exception as e:
        return {"ok": False, "message": f"Request failed: {str(e)}"}


@mcp.tool(description=(
    "Update an existing AirJaz artist with manager email information. "
    "Use when you find an email with a manager contact for an artist already in AirJaz. "
    "handle is the artist username. manager_email_exists=True if email found. "
    "summary is a short note about what the email said."
))
def update_artist_email(handle: str, manager_email_exists: bool = True, summary: str = "") -> dict:
    payload = {"handle": handle.lstrip("@").strip(), "manager_email_exists": manager_email_exists, "manager_email_summary": summary or None}
    try:
        r = httpx.patch(AIRJAZ_URL, json=payload, headers=_headers(), timeout=10)
        if r.status_code == 200:
            return {"ok": True, "message": f"Updated email intel for {handle}"}
        elif r.status_code == 404:
            return {"ok": False, "message": f"{handle} not found - add them first"}
        elif r.status_code == 401:
            return {"ok": False, "message": "Auth error - check AIRJAZ_SECRET on Render"}
        else:
            return {"ok": False, "message": f"AirJaz returned {r.status_code}: {r.text}"}
    except Exception as e:
        return {"ok": False, "message": f"Request failed: {str(e)}"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting AirJaz MCP server on port {port}")
    mcp.run(transport="http", host="0.0.0.0", port=port, stateless_http=True)
