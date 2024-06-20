#!/usr/bin/env bash
# Copyright (c) 2024 Boston Dynamics AI Institute LLC. All rights reserved.

# ======================================================
# Builds a wheel containing warp
# ======================================================

python build_lib.py
pip wheel -w dist .
