# Сравнение со штатным Ubuntu APT

Сверка проведена 6 ноября 2026 года. Эталон: Ubuntu Base 24.04.5 в
изолированной виртуальной машине, APT 2.8.3, amd64, пустой статус dpkg.
Один и тот же индекс `noble/main/binary-amd64/Packages.xz` передан
анализатору и APT. SHA-256 сжатого индекса:

```text
2a6a199e1031a5c279cb346646d594993f35b1c03dd4a82aaa0323980dd92451
```

Для проверки порядка использованы `apt-get -s` (строки `Inst`) и
`apt-get --print-uris --download-only` (список URL без скачивания).
В трёх опытах последовательности `Inst` и URL совпали между собой.
Рекомендуемые и предлагаемые пакеты отключены у обеих сторон.

| Пакет и версия | Вершины | Обязательные рёбра | Результат сверки |
| --- | --- | --- | --- |
| `hello=2.10-3build1` | 4 | 4 | Порядок и обязательные связи совпали. |
| `grep=3.11-4build1` | 5 | 6 | Связи совпали, `libc6` и `libgcc-s1` поменялись местами. |
| `sed=4.9-2build1` | 7 | 10 | Связи совпали, `libc6` и `libgcc-s1` поменялись местами. |

Фактические списки (`→` означает «дальше в списке»):

- **hello**, обе стороны: `gcc-14-base → libgcc-s1 → libc6 → hello`.
- **grep**, DFS: `gcc-14-base → libgcc-s1 → libc6 → libpcre2-8-0 → grep`.
  APT: `gcc-14-base → libc6 → libgcc-s1 → libpcre2-8-0 → grep`.
- **sed**, DFS: `gcc-14-base → libgcc-s1 → libc6 → libacl1 →`
  `libpcre2-8-0 → libselinux1 → sed`.
  APT: `gcc-14-base → libc6 → libgcc-s1 → libacl1 →`
  `libpcre2-8-0 → libselinux1 → sed`.

`libc6` требует `libgcc-s1`, а `libgcc-s1` требует `libc6`. Строгий
порядок по обеим дугам невозможен. DFS сохраняет дуги в графе и
пропускает обратную дугу при построении списка. APT планирует реальные
операции распаковки и может иначе упорядочить вершины цикла в
зависимости от корневого пакета и его `Pre-Depends`.

Для визуализации использован `apt-cache dotty`. Сравнивались обязательные
дуги из достижимых вершин, расположенных до границы глубины 3. В DOT
синие дуги соответствуют `Pre-Depends`, обычные - `Depends`. Например,
обе диаграммы `grep` содержат `grep → libc6` и `grep → libpcre2-8-0`
как предзависимости, а также обе дуги цикла `libc6 ↔ libgcc-s1`.
Сверка подтвердила 4, 6 и 10 обязательных дуг соответственно.

В штатном DOT есть дополнительные связи: например, `hello →`
`hello-traditional` и `grep → rgrep` показаны зелёным как конфликты.
D2 содержит обязательные зависимости, точные версии вершин и предел
глубины. Различия цвета, расположения и формата DOT/D2 ожидаемы.

## Повторение на Ubuntu

Скачайте и распакуйте индекс, не выполняя `apt update` или установку:

```sh
archive=https://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64
curl -fL "$archive/Packages.xz" -o Packages.xz
xz -dc Packages.xz > Packages
sh examples/compare-apt.sh Packages
```

Скрипт создаёт временные списки, пустой статус и отдельные настройки APT.
В режиме `--print-uris` разрешение на неаутентифицированные записи
применяется только к этому временно собранному кэшу: никакие пакеты
не загружаются и настройки системы не меняются. Для сравнения со своим
выводом запустите, например:

```sh
sh run.sh --config examples/ubuntu/grep.yaml --mode order
sh run.sh --config examples/ubuntu/grep.yaml --mode d2
```

Документация: [Ubuntu APT: apt-get](https://manpages.ubuntu.com/manpages/noble/man8/apt-get.8.html),
[apt-cache](https://manpages.ubuntu.com/manpages/noble/man8/apt-cache.8.html),
[Debian Policy: relationships](https://www.debian.org/doc/debian-policy/ch-relationships.html),
[D2: экспорт](https://www.d2lang.com/tour/exports/).
