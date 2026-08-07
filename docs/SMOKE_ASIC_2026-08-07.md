# ASIC smoke results (2026-08-07) — updated for v0.2.3 + 0086

Jar: `eturlia-1.21.1-neoforge-21.1.248` with patches **0083–0086**.

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
| **Supplementaries** (+ Moonlight) | draw→useAmmo, Creeper explode 6-arg, FlowerPot.addPlant, ConditionalOps |
| **quality_food** | setBlock getLightBlock, SugarCane setBlockAndUpdate, craftSlots descriptor, furnace burn 5-arg |
| Create + Aeronautics + Sable + eturlia-shim | prior PASS (0083) |
| Lithostitched ≥1.7.13 + Terralith + Incendium | prior PASS |

## Still BLOCK / document-only

| Mod | Why |
|-----|-----|
| BetterEnd / BCLib (Fabric) | Wrong loader |
| easy_npc_bundle | Empty JiJ — use separate jars |
| amendments | Not re-certified with Supplementaries on this pass |

## Pack hygiene

- Remove lithostitched beta; use ≥1.7.13
- Replace Arclight sable patch with eturlia-shim
- Remove spark-neoforge, client jars, `*.bak` / `*.jar1`
- Do not use Fabric BetterEnd stack

## Bottom line

Former ASIC BLOCKs including **Supplementaries** and **quality_food** now **boot alone** on Eturlia with 0086. Full concurrent ~60+ pack is still **not** certified green.
