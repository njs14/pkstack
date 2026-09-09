# PKStack artwork

- [logo.png](logo.png) is the owner-selected Knowledge crest used by the repository README.
- [pkstack-power.jpg](pkstack-power.jpg) is a compact 512 × 512 Power icon: the scholarly ghost, open book, and knowledge branches from the crest, simplified for a thumbnail.

These standalone files are excluded from the Power package. The compact JPG is
also embedded in `powers/pkstack/POWER.md` as an `iconUrl` data URI because Kiro
IDE 1.0.437 reads its details metadata there and blocks arbitrary remote image
hosts. Its image policy permits data URIs. This adds the 49 KB thumbnail without
shipping the full README crest. The standard `plugin.json` stays unchanged.

When replacing the JPG, refresh the `POWER.md` data URI. The Power metadata test
requires the decoded bytes to match this source image and stay below 64 KiB;
description, author, and keywords must match `plugin.json`.

[Artwork history and attribution](creation-history.md) records the source and generation prompt.
