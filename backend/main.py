#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FasoTurf Backend API (FastAPI).

Architecture imposée par le projet :

    React  →  API (routers)  →  Service  →  Repository  →  Database

Le frontend ne touche **jamais** la base : tout passe par cette API.
La base est **détectée automatiquement** (voir `backend/config.py`) et ouverte
en **lecture seule** (`mode=ro` + `PRAGMA query_only = ON`, ADR-001).

Ce module sert **aussi** l'interface compilée (`dist/`) lorsqu'elle existe : un
seul port expose alors l'application et l'API, ce qui évite toute question de
CORS ou de double serveur à maintenir.

Lancement (depuis `fasoturf/`) :

    python -m backend.main
    # ou
    python -m uvicorn backend.main:app --reload --port 8000

Puis ouvrir : http://127.0.0.1:8000
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import database_path
from .routers import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s — %(message)s",
)
logger = logging.getLogger("fasoturf.api")

FASOTURF_DIR = Path(__file__).resolve().parent.parent

#: Interface compilée par `npm run build`. Sa présence est **optionnelle** :
#: l'API fonctionne seule si le frontend n'a pas été compilé.
DIST_DIR = FASOTURF_DIR / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Vérifie au démarrage que la base a bien été détectée."""
    try:
        path = database_path()
        logger.info("Base détectée : %s", path)
        logger.info("Accès : lecture seule (mode=ro)")
    except RuntimeError as exc:
        # L'application démarre quand même : /api/health expliquera l'erreur.
        logger.error("Aucune base exploitable détectée : %s", exc)

    if DIST_DIR.is_dir():
        logger.info("Interface servie depuis : %s", DIST_DIR)
    else:
        logger.warning(
            "Interface non compilée (%s absent) : seule l'API est exposée. "
            "Lancer `npm run build` pour servir l'application.",
            DIST_DIR,
        )
    yield


app = FastAPI(
    title="FasoTurf API",
    description=(
        "API REST en lecture seule sur la base PMU / LONAB du projet. "
        "Les probabilités proviennent du moteur Hippo Engine ; les données de "
        "démonstration ne sont jamais présentées comme des résultats réels."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# CORS : utile uniquement quand l'interface est servie par le serveur Vite, sur
# un port distinct. En service groupé (un seul port) aucune requête croisée
# n'est émise.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError) -> JSONResponse:
    """Une base introuvable doit produire une réponse lisible, pas une 500 nue."""
    logger.error("Erreur d'exécution sur %s : %s", request.url.path, exc)
    return JSONResponse(
        status_code=503,
        content={
            "detail": str(exc),
            "hint": "Définissez la variable d'environnement FASOTURF_DB vers une base exploitable.",
        },
    )


@app.get("/api", include_in_schema=False)
def api_root() -> dict[str, object]:
    """Point d'entrée informatif de l'API."""
    return {
        "service": "FasoTurf API",
        "version": app.version,
        "documentation": "/docs",
        "health": "/api/health",
    }


# --------------------------------------------------------------------------
# Interface compilée (facultative)
# --------------------------------------------------------------------------

# NOTE : ces routes sont déclarées **après** l'inclusion des routeurs d'API.
# Starlette évalue les routes dans l'ordre de déclaration : `/api/...` est donc
# toujours résolu avant la route attrape-tout ci-dessous.
if DIST_DIR.is_dir():
    _assets_dir = DIST_DIR / "assets"
    if _assets_dir.is_dir():
        # Les fichiers compilés portent une empreinte dans leur nom : ils
        # peuvent être mis en cache longuement sans risque.
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

    _dist_root = DIST_DIR.resolve()

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str) -> FileResponse:
        """
        Sert l'application React.

        Une route d'interface (`/courses`, `/chevaux/…`) n'existe pas sur le
        disque : elle doit retomber sur `index.html`, sinon un rechargement de
        page renverrait 404. En revanche, un chemin `/api/...` inconnu doit
        rester un 404 d'API — jamais une page HTML.
        """
        if full_path.startswith("api/") or full_path == "api":
            raise HTTPException(status_code=404, detail="Ressource inconnue")

        if full_path:
            candidate = (DIST_DIR / full_path).resolve()
            try:
                candidate.relative_to(_dist_root)
            except ValueError:
                # Tentative de remontée hors du dossier compilé.
                raise HTTPException(status_code=404, detail="Ressource inconnue") from None
            if candidate.is_file():
                return FileResponse(candidate)

        return FileResponse(
            DIST_DIR / "index.html",
            media_type="text/html",
            headers={"Cache-Control": "no-store"},
        )

else:

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, object]:
        """Sans interface compilée, `/` décrit l'API disponible."""
        return {
            "service": "FasoTurf API",
            "version": app.version,
            "interface": "non compilée — lancer `npm run build` puis redémarrer",
            "documentation": "/docs",
            "health": "/api/health",
        }


def main() -> None:
    """Lance le serveur (interface + API sur le même port)."""
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
