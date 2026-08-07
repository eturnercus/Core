# Eturlia v0.2.3

## Highlights

Kernel bridges for ASIC pack BLOCK mods (patches **0084–0086**):

- Farmers Delight — `ItemStack`/`Item` crafting remaining
- CreativeCore — ComponentSerialization matcher + Shapes.createIndexMerger
- Let's Do Farm & Charm — void `dropAllDeathLoot`, TemptGoal/Cat Player fields
- Twilight Forest — extensible `Boat.Type` (+ DamageEffects, GrassColorModifier, ItemDisplayContext), FlowerPot Supplier ctor, `Item.Properties.setNoRepair` / `component(Supplier,…)`
- letmedespawn / horseman — `discard()V` call sites
- lodestone — `AttributeSupplier.Builder(AttributeSupplier)`
- **Supplementaries** — ProjectileWeapon `draw`→`useAmmo`, Creeper 6-arg `explode`, `FlowerPot.addPlant`, ConditionalOps for datapack registries + recipes
- **quality_food** — `Level.setBlock`/`getLightBlock`, SugarCane `setBlockAndUpdate`, `craftSlots` as `CraftingContainer`, furnace `burn` 5-arg
- Plus prior Aeronautics ComparatorBlock fix (**0083**)

## Still not green

Fabric BetterEnd stack, empty `easy_npc_bundle` JiJ; amendments not re-certified. Full concurrent ASIC pack not claimed green.

## Artifact

`eturlia-1.21.1-neoforge-21.1.248.jar` — MC 1.21.1 · NeoForge 21.1.248 · Folia

SHA256: `a3b5e0813f1a994e6c7aca77effa1f76bf314fe56d19db5b8741c9c4ec4af0ee`
