# Разбор ошибок в консоли (боевой прогон, 8 августа 2026)

Что именно шумит при старте тестового сервера `test_asic_1`, откуда берётся и что с этим делать.

## Сводка

| Ошибка | Раз за старт | Причина | Статус |
|---|---|---|---|
| `Failed to load function incendium:…` | 2231 | Folia отключила `/scoreboard` | ограничение Folia |
| `Unexpected exception while parsing console command` | по команде | то же самое | ограничение Folia |
| `Essentials: ExceptionInInitializerError` | 1 | ядро отдавало `Unknown-Version` | **исправлено** |
| `Could not load plugin 'WorldEdit'` | 1 | api-version 1.21.4 / нет Folia | **исправлено** |
| ChunkHeatMap `NoSuchMethodError` + watchdog 10.7 с | постоянно | плагин собран под API 1.21.4 | **исправлено** |
| `DimensionDataStorage: aeronautics_unloaded_balloons` | 3 | Create Aeronautics | открыто |
| `entities have not registered to RegisterSpawnPlacementsEvent` | 1 | `minecraft:camel` | косметика |
| `No data fixer registered for …` | ~12 | сущности Create | косметика |

## 1. 2231 ошибок датапаков — `/scoreboard` вырезан в Folia

Корень в патче Folia `0003-Threaded-Regions`:

```java
//ScoreboardCommand.register(this.dispatcher, commandRegistryAccess); // Folia - region threading - TODO later
```

Folia убирает `/scoreboard`, потому что таблички — глобальное состояние, а команды выполняются на
региональных потоках. Это не дефект Eturlia и не следствие наших патчей: **в логах от 7 августа,
до всех изменений, ровно те же 2231**.

Дальше идёт каскад. Аргумент `minecraft:function` проверяет ссылку **на этапе парсинга**, поэтому
одна несуществующая функция валит всех, кто её зовёт:

```
data/incendium/function/border_of_life/notes/319.mcfunction, строка 7:
    scoreboard players set @s nbs_borderofli_t 319
    → Unknown or incomplete command at position 0
```

Из 2231 ошибок 1753 — это `incendium:border_of_life`, музыкальная система на нот-блоках, целиком
построенная на scoreboard. Она не заработает ни на одном Folia-сервере.

**Варианты:**

- *Ничего не делать.* Ошибки уходят в `logs/eturlia-noise.log`, консоль чистая. Ломается только
  музыка Incendium; остальной контент мода работает.
- *Убрать музыкальный датапак* — исчезнут 1753 из 2231.
- *Вернуть `/scoreboard`.* Одна строка в патче 0003 плюс выполнение команды на глобальном регионе.
  Folia пометила это «TODO later» именно из-за потокобезопасности: таблички читаются и пишутся из
  разных регионов. Делать это стоит осознанно, отдельной задачей и с нагрузочным тестом.

## 2. EssentialsX падал и уносил с собой `help`, `list` и остальные команды — исправлено

```
Caused by: IllegalArgumentException: Unknown-Version is not in valid version format. e.g. 1.8.8-R0.1
```

Плагин регистрирует свои команды, потом падает при включении — и каждая из них остаётся в карте
команд, указывая на выключенный плагин:

```
CommandException: Cannot execute command 'help' in plugin Essentials - plugin is disabled.
```

Две причины, обе в ядре:

1. **Версия проекта была не в формате Bukkit.** `settings.gradle.kts` собирал
   `1.21.1.local-SNAPSHOT`, а Bukkit требует `<mc>-R<ревизия>`. Теперь `1.21.1-R0.1-SNAPSHOT`.
2. **`EturliaGameLocator` выбрасывал весь `META-INF/` из folia-api.** Это делалось, чтобы MANIFEST
   Folia AT не был перебит (CraftBukkit читает оттуда дату сборки), но заодно выбрасывался
   `META-INF/maven/dev.folia/folia-api/pom.properties` — единственное место, откуда
   `Bukkit.getBukkitVersion()` берёт версию. Теперь отбрасываются только `MANIFEST.MF` и подписи,
   вложенные данные вроде `META-INF/maven/**` остаются.

После этого включаются все четыре плагина: ChunkHeatMap, ChunkHeatMapAdmin, WorldEdit, Essentials —
и `/list` отвечает.

## 3. WorldEdit — исправлено подбором сборки

Плагин проходит две независимые проверки, и обычный WorldEdit валится на обеих:

| Сборка | api-version | folia-supported | Результат |
|---|---|---|---|
| `worldedit-bukkit-7.4.1-SNAPSHOT` (WorldEdit-Folia) | 1.21.4 | да | отказ: сервер 1.21.1 |
| `worldedit-bukkit-7.3.10-beta-01` (обычный) | 1.20 | **нет** | отказ: не поддерживает Folia |
| **`worldedit-bukkit-7.3.9` (WorldEdit-Folia, тег 7.3.8.1)** | **1.13** | **да** | **загружается** |

Стоит именно последняя. Более свежие сборки WorldEdit-Folia нацелены на 1.21.3+ и на 1.21.1 не
встанут, пока проект не выпустит билд под нашу версию.

## 4. Что осталось открытым

- **`aeronautics_unloaded_balloons`** — `DimensionDataStorage` не может прочитать сохранённые данные
  Create Aeronautics (3 раза за старт, по одному на мир). Похоже на несовместимость мода с
  региональным хранилищем; нужен отдельный разбор.
- **`minecraft:camel` не зарегистрирован в `RegisterSpawnPlacementsEvent`** — предупреждение
  NeoForge, на игру не влияет.
- **`No data fixer registered for …`** — ваниль ругается на сущности Create, косметика.

## Куда смотреть

Консоль теперь показывает одну строку на ошибку. Полный текст со стектрейсами:

```
logs/eturlia-noise.log     ← стектрейсы третьих сторон (может быть несколько МБ)
logs/eturlia.log           ← собственная диагностика Eturlia
logs/latest.log            ← полный лог сервера, без фильтрации
```

Выключить фильтр: `-Deturlia.console.noise=off`.
