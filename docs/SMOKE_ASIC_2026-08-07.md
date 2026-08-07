# ASIC smoke results (2026-08-07) — updated for v0.2.3

Jar: `eturlia-1.21.1-neoforge-21.1.248` with patches **0083–0085** (ComparatorBlock + ASIC BLOCK bridges).

**Legend:** boot = FML OK + `Done (...)!`. Not gameplay / region-safe proof.

## Confirmed PASS (individual smoke)

| Mod / set | Notes |
|-----------|--------|
| Farmers Delight | `ItemStack.getCraftingRemainingItem` |
| CreativeCore | ComponentSerialization + Shapes.createIndexMerger |
| Let's Do Farm & Charm | void `dropAllDeathLoot`, TemptGoal/Cat Player fields |
| Twilight Forest | extensible enums + FlowerPot Supplier + `setNoRepair` |
| letmedespawn (+ Almanac) | `discard()V` in checkDespawn |
| lodestone | AttributeSupplier.Builder copy-ctor |
| horseman | leash `discard()V` |
| Create + Aeronautics + Sable + eturlia-shim | prior PASS (0083) |
| Lithostitched ≥1.7.13 + Terralith + Incendium | prior PASS |

## Still BLOCK / FAIL

| Mod | Why |
|-----|-----|
| Supplementaries (+ amendments) | Further Folia mixin gaps (e.g. ProjectileWeaponItem) after travel/Fire/onItemUse fixes |
| quality_food | Level.setBlock / getLightBlock inject vs Paper rewrite |
| BetterEnd / BCLib (Fabric) | Wrong loader |
| easy_npc_bundle | Empty JiJ — use separate jars |

## Pack hygiene

- Remove lithostitched beta; use ≥1.7.13
- Replace Arclight sable patch with eturlia-shim
- Remove spark-neoforge, client jars, `*.bak` / `*.jar1`
- Do not use Fabric BetterEnd stack

## Bottom line

Many former ASIC BLOCKs now **boot alone** on Eturlia v0.2.3. Full concurrent ~60+ pack is still **not** certified; peel remaining Supplementaries/quality_food and junk before claiming green.
