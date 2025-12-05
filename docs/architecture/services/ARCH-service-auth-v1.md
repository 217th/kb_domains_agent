---
id: ARCH-service-auth
title: "Service: Authentication"
type: service
layer: infrastructure
owner: @team-core
version: v1
status: current
created: 2025-12-02
updated: 2025-12-02
tags: [auth, firestore]
depends_on: []
referenced_by: []
---
## Context
Provides user identity resolution and creation backed by Firestore.

## Structure
*   **File:** `src/tools/auth.py`
*   **Key Function:** `tool_auth_user(payload)`

## Behavior
*   **Lookup:** Queries the `users` collection in Firestore by `username`.
*   **Creation:** If the user does not exist, creates a new document and returns the new `user_id`.
*   **Output:** Returns `user_id` and `is_new_user` flag.

## Evolution
### Historical
*   v1: Firestore-backed username lookup and auto-creation.
