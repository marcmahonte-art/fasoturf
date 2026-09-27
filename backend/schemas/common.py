#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Types partagés par les schémas de l'API."""

from __future__ import annotations

from typing import Literal

#: Provenance d'une donnée exposée au frontend (spec §2.3).
DataOrigin = Literal["real", "prediction", "official", "demo"]

#: Cycle de vie d'une course.
RaceStatus = Literal["upcoming", "live", "finished", "suspended"]
