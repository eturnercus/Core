<div align="center">
    <img src="./folia.png" alt="Crelia" width="720">
    <h1>Crelia</h1>
    <p>Многопоточные регионы Folia + загрузка модов NeoForge — серверное ядро Minecraft <strong>1.21.1</strong>.</p>

    <!-- Плашки статуса — НЕ для продакшена -->
    ![Статус](https://img.shields.io/badge/статус-экспериментальный-orange?style=for-the-badge)
    ![Продакшен](https://img.shields.io/badge/продакшен-НЕТ-red?style=for-the-badge)
    ![Стабильность](https://img.shields.io/badge/стабильность-pre--release-yellow?style=for-the-badge)
    ![Minecraft](https://img.shields.io/badge/Minecraft-1.21.1-62B47A?style=for-the-badge&logo=minecraft)
    ![NeoForge](https://img.shields.io/badge/NeoForge-21.1.248-3B82F6?style=for-the-badge)
    ![Java](https://img.shields.io/badge/Java-21-007396?style=for-the-badge&logo=openjdk&logoColor=white)

    <p><strong><a href="#плашки-статуса">→ Что означают плашки</a></strong> · <strong><a href="#english">🇬🇧 English version</a></strong></p>
</div>

> [!CAUTION]
> **Не для продакшена.** Экспериментальная сборка: загрузка NeoForge-модов через ModLauncher ещё не завершена, многие моды несовместимы с региональным многопоточностью Folia. Делайте бэкапы миров перед запуском.

## Плашки статуса

| Плашка | Значение |
|--------|----------|
| **статус — экспериментальный** | Проект в активной разработке; API, патчи и поведение могут меняться без предупреждения. |
| **продакшен — НЕТ** | **Не используйте на основном сервере или с живым сейвом.** Только для тестов, разработки и экспериментов. |
| **стабильность — pre-release** | Релизы помечены как pre-release на GitHub; это не стабильная ветка для публичных серверов. |
| **Minecraft / NeoForge / Java** | Целевые версии стека; совместимость с другими версиями не гарантируется. |

## Что это

Crelia собирает **один fat-jar серверного ядра**, объединяющий:

- **[Folia](https://github.com/PaperMC/Folia)** — форк Paper с многопоточной обработкой по регионам
- **[NeoForge](https://github.com/neoforged/NeoForge) 21.1.248** — последний NeoForge для MC 1.21.1 (FancyModLoader 4.0.43)

**Цель:** запускать тех-модпаки (Create и др.) на многопоточной региональной модели Folia.

## Версии

| Компонент | Версия |
|-----------|--------|
| Minecraft | 1.21.1 |
| NeoForge | **21.1.248** (последний 21.1.x) |
| FML (FancyModLoader) | 4.0.43 |
| Paper upstream | `84281ceeefb9d294758a9a292ba6c01da40e8409` (Folia `dev/1.21.1`) |
| Java | 21 |

## Сборка

Нужен **git clone** (не ZIP), **JDK 21** и доступ к Maven PaperMC и NeoForged.

```bash
# 1) Применить патчи Folia + Crelia/NeoForge поверх Paper
./gradlew applyPatches

# 2) Собрать Folia-Server (reobf / paperclip как обычно)
./gradlew :folia-server:build

# 3) Собрать standalone fat-jar ядра
./gradlew :folia-server:creliaStandaloneJar
```

Результат:

```text
build/libs/crelia-1.21.1-neoforge-21.1.248.jar
```

Сокращения:

```bash
./patch.sh          # applyPatches
./rb.sh             # пересборка Paper/server/minecraft патчей
```

## Запуск

```bash
java -jar build/libs/crelia-1.21.1-neoforge-21.1.248.jar
```

Лauncher распаковывает вложенные библиотеки и запускает `crelia.CreliaServer` с аргументами FML для MC 1.21.1 / NeoForge 21.1.248.

При первом запуске примите `eula.txt`. NeoForge-моды — в `mods/`. Плагины должны иметь `folia-supported: true`.

> [!WARNING]
> FML mod scan через ModLauncher пока не полностью владеет запуском — моды в `mods/` могут не загрузиться. Хуки NeoForge lifecycle могут писать WARN — сервер при этом может дойти до `Done`.

## Релизы

Готовые сборки — в [GitHub Releases](https://github.com/eturnercus/Core/releases). Все релизы помечены **Pre-release** и **не предназначены для продакшена**.

## Архитектура (кратко)

1. **paperweight 1.7.3** применяет `patches/api` + `patches/server` (региональные патчи Folia + NeoForge event hooks) поверх Paper.
2. **Shims** в `build-data/crelia-neoforge-shims` позволяют скомпилировать пропатченные исходники Minecraft против заглушек NeoForge API.
3. **NeoForge universal** `21.1.248` встраивается в runtime (не дерево NeoForge для MC 26 из старых форков Crelia).
4. **Coremods** используют NeoForge 21.1 SPI `ICoreMod` (не API FML 7 `ClassProcessorProvider`).
5. **Crelia launcher** поставляет fat-jar: Folia server + FML + NeoForge + Crelia runtime.

## Upstream

- [PaperMC/Folia](https://github.com/PaperMC/Folia) (`dev/1.21.1`)
- [PaperMC/Paper](https://github.com/PaperMC/Paper)
- [NeoForged/NeoForge](https://github.com/neoforged/NeoForge) (`1.21.1` / 21.1.x)
- Референсные форки: [holynwk/Crelia](https://github.com/holynwk/Crelia), [SOURsLEMONS/Crelia](https://github.com/SOURsLEMONS/Crelia)

## Лицензия

Разные части дерева — под разными лицензиями. Патчи Folia/Paper: [`PATCHES-LICENSE`](./PATCHES-LICENSE). Код NeoForge: upstream LGPL / заголовки файлов.

## Статус патчей

Активные серверные патчи: Folia `0001`–`0019` + NeoForge hooks `0020`–`0025` (API выровнен под NeoForge **21.1.248**).

Дополнительные батчи NeoForge hooks `0033`–`0040` лежат в `patches/server-wip/` — написаны под неполные shims и пока не применяются чисто. Будут перебазированы на 21.1.248 позже.

---

<details id="english">
<summary><strong>🇬🇧 English version</strong></summary>

<div align="center">
    <h1>Crelia</h1>
    <p>Folia region threading + NeoForge mod loading — Minecraft <strong>1.21.1</strong> server kernel.</p>

    ![Status](https://img.shields.io/badge/status-experimental-orange?style=for-the-badge)
    ![Production](https://img.shields.io/badge/production-NO-red?style=for-the-badge)
    ![Stability](https://img.shields.io/badge/stability-pre--release-yellow?style=for-the-badge)
    ![Minecraft](https://img.shields.io/badge/Minecraft-1.21.1-62B47A?style=for-the-badge&logo=minecraft)
    ![NeoForge](https://img.shields.io/badge/NeoForge-21.1.248-3B82F6?style=for-the-badge)
    ![Java](https://img.shields.io/badge/Java-21-007396?style=for-the-badge&logo=openjdk&logoColor=white)
</div>

> [!CAUTION]
> **Not for production.** Experimental build: NeoForge mod loading via ModLauncher is incomplete; many mods are incompatible with Folia regionized threading. Back up worlds before running.

### Status badges

| Badge | Meaning |
|-------|---------|
| **status — experimental** | Active development; APIs, patches, and behavior may change without notice. |
| **production — NO** | **Do not run on a live server or primary world save.** Testing and development only. |
| **stability — pre-release** | GitHub releases are marked pre-release; not a stable branch for public servers. |
| **Minecraft / NeoForge / Java** | Target stack versions; other versions are unsupported. |

### What this is

Crelia builds a **single server core fat jar** combining:

- **[Folia](https://github.com/PaperMC/Folia)** — Paper fork with per-region multi-threading
- **[NeoForge](https://github.com/neoforged/NeoForge) 21.1.248** — latest NeoForge for MC 1.21.1 (FancyModLoader 4.0.43)

Goal: run Create / tech-mod packs on Folia’s multi-core region model.

### Versions

| Component | Version |
|-----------|---------|
| Minecraft | 1.21.1 |
| NeoForge | **21.1.248** (latest 21.1.x) |
| FML (FancyModLoader) | 4.0.43 |
| Paper upstream | `84281ceeefb9d294758a9a292ba6c01da40e8409` (Folia `dev/1.21.1`) |
| Java | 21 |

### Build

Requires **Git clone** (not a ZIP), **JDK 21**, and network access to PaperMC + NeoForged Maven.

```bash
./gradlew applyPatches
./gradlew :folia-server:build
./gradlew :folia-server:creliaStandaloneJar
```

Output: `build/libs/crelia-1.21.1-neoforge-21.1.248.jar`

### Run

```bash
java -jar build/libs/crelia-1.21.1-neoforge-21.1.248.jar
```

Accept `eula.txt` on first run. NeoForge mods go in `mods/`. Plugins need `folia-supported: true`.

> [!WARNING]
> FML mod scan via ModLauncher does not fully own startup yet — mods in `mods/` may not load. NeoForge lifecycle hooks may log WARNs while the server still reaches `Done`.

### Releases

Pre-built jars are on [GitHub Releases](https://github.com/eturnercus/Core/releases). All releases are **Pre-release** and **not production-ready**.

### Architecture (short)

1. **paperweight 1.7.3** applies `patches/api` + `patches/server` onto Paper.
2. **Shims** under `build-data/crelia-neoforge-shims` let patched Minecraft sources compile against NeoForge API stubs.
3. **Published NeoForge universal** `21.1.248` is embedded at runtime.
4. **Coremods** use NeoForge 21.1 `ICoreMod` SPI.
5. **Crelia launcher** ships a fat jar with Folia server + FML + NeoForge + Crelia runtime.

### Upstream

- [PaperMC/Folia](https://github.com/PaperMC/Folia) (`dev/1.21.1`)
- [PaperMC/Paper](https://github.com/PaperMC/Paper)
- [NeoForged/NeoForge](https://github.com/neoforged/NeoForge) (`1.21.1` / 21.1.x)
- Reference forks: [holynwk/Crelia](https://github.com/holynwk/Crelia), [SOURsLEMONS/Crelia](https://github.com/SOURsLEMONS/Crelia)

### License

Different trees use different licenses. Folia/Paper patches: [`PATCHES-LICENSE`](./PATCHES-LICENSE). NeoForge code: upstream LGPL / file headers.

### Patch status

Active server patches: Folia `0001`–`0019` + NeoForge hooks `0020`–`0025` (API-aligned to NeoForge **21.1.248**).

Additional NeoForge hook batches `0033`–`0040` are under `patches/server-wip/` and do not apply cleanly yet.

</details>
