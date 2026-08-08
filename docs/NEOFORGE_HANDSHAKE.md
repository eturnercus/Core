# NeoForge network handshake (patch 0095)

## Симптом

Клиент с NeoForge-модами не мог зайти на сервер:

```
Соединение потеряно
Вы пытаетесь подключиться к серверу, который не использует NeoForge,
но у вас есть моды, требующие этого. Не удалось установить подключение.
```

Вторая попытка падала иначе:

```
Соединение потеряно
Internal Exception: java.lang.UnsupportedOperationException
```

В логах сервера при этом **ничего** — обе ошибки возникали на стороне клиента.

## Причина

Eturlia — это Folia (CraftBukkit-дерево) плюс рантайм NeoForge. Классы сетевого слоя брались
ванильные, без патчей NeoForge, поэтому модовая часть протокола не существовала:

1. `ServerConfigurationPacketListenerImpl.startConfiguration()` сразу шёл в ванильную
   конфигурацию. Сервер ни разу не отправлял `neoforge:register` — для клиента он выглядел
   как обычный ванильный сервер, и клиент отказывался подключаться.
2. Кодек кастомных пейлоадов знал только ванильные каналы. Любая попытка отправить пейлоад
   NeoForge падала в энкодере:
   ```
   ClassCastException: MinecraftUnregisterPayload cannot be cast to DiscardedPayload
   ```
   Netty закрывал канал, клиент показывал `Internal Exception: ...`.

## Что делает патч

Повторяет патчи NeoForge 1.21.1 для этих классов, адаптированные под форму CraftBukkit/Folia.

### Порядок конфигурации

`startConfiguration()` больше не запускает ванильную конфигурацию напрямую. Сначала идёт
согласование каналов:

```java
send(MinecraftUnregisterPayload(NetworkRegistry.getInitialServerUnregisterChannels()));
send(MinecraftRegisterPayload(NetworkRegistry.getInitialListeningChannels(flow())));
send(ModdedNetworkQueryPayload(Map.of()));
send(new ClientboundPingPacket(0));
```

Ванильное тело переехало в `eturliaRunConfiguration()` и запускается из `handlePong()` при
получении pong с id 0:

- клиент ответил `ModdedNetworkQueryPayload` → `connectionType = NEOFORGE` и
  `NetworkRegistry.initializeNeoForgeConnection(...)`;
- клиент промолчал (ванильный) → `NetworkRegistry.initializeOtherConnection(...)`, и если тот
  отказывает, конфигурация не запускается вовсе.

Плюс `ConfigurationInitialization.configureEarlyTasks(...)` до `SynchronizeRegistriesTask`
(реестры должны синхронизироваться раньше, чем ваниль отправит теги) и задачи модов из
`RegisterConfigurationTasksEvent`.

### Кодеки пейлоадов

`CustomPacketPayload.codec(...)` получил параметры `ConnectionProtocol` и `PacketFlow`, а поиск
кодека спрашивает реестр модов прежде, чем свалиться в ванильный «выбросить неизвестный
пейлоад»:

```java
if (streamCodec == null) {
    streamCodec = NetworkRegistry.getCodec(id, protocol, packetFlow);
}
```

Оба вызова в `ClientboundCustomPayloadPacket` (PLAY и CONFIGURATION) и вызов в
`ServerboundCustomPayloadPacket` передают эти параметры.

### Интерфейсы слушателей

NeoForge вызывает `listener.getConnection()` и `getConnectionType()` через **invokeinterface** по
`ServerConfigurationPacketListener`. Реализация только на классе тут не спасает — JVM резолвит
метод по интерфейсу и без объявления бросает `NoSuchMethodError`. Поэтому
`ServerCommonPacketListener` расширяет `ICommonPacketListener`, а `ServerCommonPacketListenerImpl`
реализует его методы и обрабатывает register/unregister/common-version/common-register и модовые
пейлоады.

### Аксессоры Connection

`NetworkFilters.injectIfNecessary()` зовёт `Connection.channel()`, которого в дереве не было —
handshake падал с `NoSuchMethodError: Connection.channel()`, а клиент опять видел только
`Internal Exception`. Добавлены `channel()` и `getDirection()`.

### Поток выполнения

`handlePong()` приходит на сетевом/региональном потоке, а ванильное тело конфигурации вызывает
CraftBukkit-событие `PlayerLinksSendEvent`, которое допускается только с главного потока:

```
IllegalStateException: PlayerLinksSendEvent may only be triggered synchronously.
```

Поэтому `eturliaRunConfiguration()` отправляется в очередь сервера (`server.execute`), то есть
на глобальный регион в Folia.

## Проверка

`scripts/join-probe.py` говорит по протоколу 1.21.1 напрямую, без библиотек Minecraft: статус,
логин со сжатием, фаза конфигурации. Умеет вести себя и как ванильный, и как NeoForge-клиент.

Против собранного ядра:

```
configuration payloads received: 4
  minecraft:unregister
  minecraft:register
  neoforge:register
  neoforge:modded_network_setup_failed

PASS  server announces the modded network
PASS  NeoForge-speaking client was not rejected for missing NeoForge
PASS  no UnsupportedOperationException during login/configuration
```

Ванильный пробник теперь получает зеркальный отказ — то есть сервер стал полноценным
NeoForge-сервером:

```
lost connection: You are trying to connect to a server that is running NeoForge,
but you are not. Please install NeoForge to connect to this server.
```

`neoforge:modded_network_setup_failed` в прогоне — **ожидаемо**: пробник заявляет пустой список
каналов. Настоящий клиент присылает свой набор каналов и получает успешное согласование. Полный
успешный modded-handshake требует клиента с тем же набором модов и этим скриптом не проверяется.

## Как править патчи этого дерева

Осторожно: `paperweight` применяет набор через `git am --3way`, и это накладывает два правила.

1. **Хунк без изменений — битый патч.** Если убрать из хунка последнюю `+`-строку, останутся
   только контекстные строки, и `git am` отвечает `corrupt patch`. `scripts/check-patches.py`
   это ловит.
2. **Патчить ванильный файл можно только диффом-модификацией.** paperweight сам подкладывает
   любой упомянутый в патче mc-dev файл в `src/main/java` перед `git am`, поэтому секция с
   `new file mode` / `--- /dev/null` для такого файла даёт `CONFLICT (add/add)` и валит весь
   набор. Именно на это умер прошлый заход (PR #28). После `./gradlew rebuildPatches` прогоняйте
   `scripts/fix-newfile-patches.py <patch>` — он переписывает такие секции в обычный дифф с
   настоящими blob-хэшами.
3. Патч можно править руками только если он **последний**, кто трогает свои файлы: правка меняет
   post-image хэш, а следующие патчи по тому же файлу ссылаются на него в `index`.

Ещё нюанс: файл, который до сих пор не патчился, никогда и не компилировался из исходника.
`CustomPacketPayload` при первом же патче не собрался — в декомпиляции пропал каст:

```java
StreamCodec<B, T> streamCodec = (StreamCodec<B, T>) this.findCodec(id.id);
```

Такое ждите на каждом новом ванильном файле.
