"""
benchmark.py - Етап 3: порівняльне дослідження.

Цей скрипт ганяє однакові операції (INSERT, SELECT, UPDATE, DELETE)
на кожній реалізації дерева (AVL, Splay, RB, B-дерево, B+ дерево),
а також на справжній СУБД SQLite (для порівняння). Потім за результатами
малює гарні графіки в темній темі та зводить усе в зручні таблиці.

Як запустити з терміналу:

    python benchmark.py
        Запуск зі стандартними налаштуваннями: розміри N = 1000, 2500, 5000,
        10000, 25000, 50000, по 1 повтору на кожне виконання, тестуються всі
        дерева (AVL, Splay, RB, B-дерево, B+ дерево) та SQLite. Результати
        складаються у каталог results/.

    python benchmark.py --sizes 1000 5000 10000 25000 50000 --repeats 3
        Власний список розмірів N (тут: 1000, 5000, 10000, 25000, 50000) і
        по 3 повтори кожного прогону - підсумкове значення часу береться як
        медіана з трьох вимірювань. Більше повторів - стабільніший результат,
        але довше чекати.

    python benchmark.py --quick
        Швидка «димова» перевірка на маленьких N - щоб переконатися, що
        скрипт взагалі запускається, графіки малюються, а таблиці пишуться.
        Зручно перед повним прогоном.

    python benchmark.py --no-splay --no-bplus
        Вимкнути окремі структури з тестування. Тут пропускаються splay-
        дерево та B+ дерево; решта (AVL, RB, B-дерево, SQLite) тестуються
        як звичайно. Аналогічно працюють --no-avl, --no-rb, --no-btree,
        --no-sqlite - можна комбінувати у будь-якому порядку.

Усі результати зберігаються у каталог results/:
    results/raw_results.csv         - повні «сирі» дані
    results/tables/summary_<op>.csv - зведена таблиця по кожній операції
    results/plots/lines_all.png     - графіки часу від N (усі 4 операції)
    results/plots/lines_<op>.png    - окремий графік для кожної операції
    results/plots/bars_<op>.png     - стовпчикова діаграма для найбільшого N
"""

import argparse
import csv
import gc
import os
import random
import statistics
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import visual

def _noop(*args, **kwargs):
    return None

visual.save_tree_snapshot = _noop
visual.set_label = _noop

from avl_tree import AVL_Tree
from splay_tree import Splay_tree
from rb_tree import RBTree
from b_tree import BTree
from b_plus_tree import BPlusTree
from database import Record

try:
    import sqlite3
    HAS_SQLITE = True
except ImportError:
    HAS_SQLITE = False


if sys.platform == "win32":
    try:
        os.system("chcp 65001 > NUL")
    except Exception:
        pass
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


DARK = {
    "bg":     "#111318",
    "panel":  "#1a1d26",
    "grid":   "#2a2f3d",
    "text":   "#f0f0f0",
    "title":  "#6ab0f5",
    "muted":  "#7a8090",
    "accent": "#5dbb6e",
}

ENGINE_COLORS = {
    "AVL":     "#4dab6e",
    "Splay":   "#d4a820",
    "RB":      "#e05c6a",
    "B-дерево":  "#4a7fd4",
    "B+ дерево": "#ff8c42",
    "SQLite":  "#c074ff",
}

OPS = ("INSERT", "SELECT", "UPDATE", "DELETE")


def setup_dark_style():
    """Налаштовує matplotlib під темну тему - один раз перед побудовою графіків."""
    plt.rcParams.update(
        {
            "figure.facecolor":  DARK["bg"],
            "savefig.facecolor": DARK["bg"],
            "axes.facecolor":    DARK["panel"],
            "axes.edgecolor":    DARK["grid"],
            "axes.labelcolor":   DARK["text"],
            "axes.titlecolor":   DARK["title"],
            "axes.titleweight":  "bold",
            "axes.titlesize":    13,
            "axes.labelsize":    11,
            "xtick.color":       DARK["text"],
            "ytick.color":       DARK["text"],
            "xtick.labelsize":   9,
            "ytick.labelsize":   9,
            "grid.color":        DARK["grid"],
            "grid.linestyle":    "--",
            "grid.alpha":        0.6,
            "legend.facecolor":  DARK["panel"],
            "legend.edgecolor":  DARK["grid"],
            "legend.labelcolor": DARK["text"],
            "text.color":        DARK["text"],
            "font.family":       "monospace",
            "lines.linewidth":   2.0,
            "lines.markersize":  6,
            "figure.dpi":        110,
        }
    )


class Engine:
    """Спільний інтерфейс для всього, що ми тестуємо.

    Не важливо, що це - AVL-дерево, B+ дерево чи SQLite: бенчмарк звертається
    до них однаково: setup → insert/select/update/delete → teardown.
    """

    name = "Engine"
    color = "#888888"

    def setup(self):
        """Створює структуру/відкриває з'єднання перед прогоном."""

    def insert(self, k, v):
        """Вставити запис з ключем k та значенням v."""

    def select(self, k):
        """Знайти запис за ключем. Повертає True, якщо знайдено."""

    def update(self, k, v):
        """Оновити значення запису з ключем k."""

    def delete(self, k):
        """Видалити запис з ключем k."""

    def teardown(self):
        """Прибрати за собою після прогону (звільнити пам'ять, закрити з'єднання)."""


class TreeEngine(Engine):
    """Адаптер для будь-якого з наших дерев у проєкті (AVL, Splay, RB, B, B+)."""

    def __init__(self, name, factory):
        self.name = name
        self.color = ENGINE_COLORS.get(name, "#888888")
        self.factory = factory
        self.tree = None

    def setup(self):
        self.tree = self.factory()

    def insert(self, k, v):
        self.tree.add(Record(k, v))

    def select(self, k):
        found, _ = self.tree.find(Record(k, None))
        return found

    def update(self, k, v):
        """Знаходимо вузол і переписуємо value у місці - так чесніше:
        ми реально вимірюємо пошук + перезапис, як це робить SQL UPDATE."""
        found, result = self.tree.find(Record(k, None))
        if found:
            rec = result.data if hasattr(result, "data") else result
            rec.value = v

    def delete(self, k):
        self.tree.delete(Record(k, None))

    def teardown(self):
        """Скидаємо посилання і просимо збирача сміття почистити пам'ять,
        щоб наступне виконання стартувало у «чистих» умовах."""
        self.tree = None
        gc.collect()


class SQLiteEngine(Engine):
    """Обгортка над SQLite - щоб порівняти наші дерева зі справжньою СУБД."""

    name = "SQLite"
    color = ENGINE_COLORS["SQLite"]

    def __init__(self, in_memory=True, path=":memory:"):
        """За замовчуванням працюємо в пам'яті - без диска швидше,
        і порівняння з нашими деревами стає чеснішим (вони теж у RAM)."""
        self.in_memory = in_memory
        self.path = ":memory:" if in_memory else path
        self.conn = None
        self.cur = None

    def setup(self):
        """Відкриваємо з'єднання та вимикаємо автокоміт-логіку і fsync -
        інакше час «з'їсть» диск, а ми хочемо порівнювати швидкість
        самих структур даних."""
        self.conn = sqlite3.connect(self.path)
        self.conn.isolation_level = None
        self.cur = self.conn.cursor()
        self.cur.execute("PRAGMA journal_mode = MEMORY")
        self.cur.execute("PRAGMA synchronous = OFF")
        self.cur.execute("DROP TABLE IF EXISTS bench")
        self.cur.execute("CREATE TABLE bench (k INTEGER PRIMARY KEY, v TEXT)")

    def insert(self, k, v):
        self.cur.execute("INSERT INTO bench(k, v) VALUES(?, ?)", (k, v))

    def select(self, k):
        self.cur.execute("SELECT v FROM bench WHERE k = ?", (k,))
        return self.cur.fetchone() is not None

    def update(self, k, v):
        self.cur.execute("UPDATE bench SET v = ? WHERE k = ?", (v, k))

    def delete(self, k):
        self.cur.execute("DELETE FROM bench WHERE k = ?", (k,))

    def teardown(self):
        try:
            if self.cur:
                self.cur.close()
            if self.conn:
                self.conn.close()
        except Exception:
            pass


class BenchResult:
    """Результат одного прогону: скільки часу зайняла кожна з 4 операцій.

    Поля:
        engine   - назва структури/СУБД
        n        - розмір даних
        op_total - словник {операція: загальний_час_у_секундах}
    """

    def __init__(self, engine, n, op_total=None):
        self.engine = engine
        self.n = n
        self.op_total = op_total if op_total is not None else {}

    @property
    def op_per_op_us(self):
        """Середній час однієї операції - у мікросекундах. Найзручніша одиниця для порівняння."""
        return {op: (t / max(self.n, 1)) * 1e6 for op, t in self.op_total.items()}

    @property
    def ops_per_sec(self):
        """Скільки операцій встигає за секунду - на випадок, якщо хочеться «throughput»."""
        return {op: (self.n / t if t > 0 else float("inf")) for op, t in self.op_total.items()}


def _value_for(k):
    """Генерує невелике «псевдо-JSON» значення для запису з ключем k.

    Беремо щось схоже на реальні дані, а не просто число, - щоб тести
    були ближчі до справжнього використання.
    """
    return f'{{"name": "rec{k}", "tag": "T{k % 100}"}}'


def benchmark_single_run(engine, keys_insert, keys_select, keys_update, keys_delete):
    """Одне виконання усіх 4 операцій на одному двигуні.

    Повертає словник {назва_операції: час_у_секундах}.

    На час вимірювань вимикаємо збирач сміття - інакше він може
    «вистрелити» посеред операції і зіпсувати показники.
    """
    times = {}
    engine.setup()

    gc.collect()
    gc.disable()
    try:
        t0 = time.perf_counter()
        for k in keys_insert:
            engine.insert(k, _value_for(k))
        times["INSERT"] = time.perf_counter() - t0

        t0 = time.perf_counter()
        for k in keys_select:
            engine.select(k)
        times["SELECT"] = time.perf_counter() - t0

        t0 = time.perf_counter()
        for k in keys_update:
            engine.update(k, _value_for(k) + "_upd")
        times["UPDATE"] = time.perf_counter() - t0

        t0 = time.perf_counter()
        for k in keys_delete:
            engine.delete(k)
        times["DELETE"] = time.perf_counter() - t0
    finally:
        gc.enable()
        engine.teardown()

    return times


def run_benchmark(engines, sizes, repeats=1, seed=42, verbose=True):
    """Виконує всі сценарії (усі двигуни × усі розміри × повтори) та збирає результати.

    Якщо повторів більше одного - для кожної операції беремо МЕДІАНУ часу.
    Медіана краща за середнє: вона стійка до випадкових «виплесків»,
    коли система раптом відволіклася на щось своє.

    Для кожного N готуємо ОДИН і той самий набір ключів і даємо його
    всім двигунам - щоб порівняння було чесним.
    """
    results = []

    for n in sizes:
        rnd = random.Random(seed)
        keys_insert = list(range(n))
        rnd.shuffle(keys_insert)
        keys_select = [rnd.choice(keys_insert) for _ in range(n)]
        keys_update = [rnd.choice(keys_insert) for _ in range(n)]
        keys_delete = list(keys_insert)
        rnd.shuffle(keys_delete)

        for eng in engines:
            run_times = {op: [] for op in OPS}
            ok = True
            for r in range(repeats):
                if verbose:
                    print(f"  > {eng.name:<11} | N={n:>6} | виконання {r+1}/{repeats} ...", end="", flush=True)
                try:
                    t = benchmark_single_run(eng, keys_insert, keys_select, keys_update, keys_delete)
                    for op, val in t.items():
                        run_times[op].append(val)
                    if verbose:
                        print("  " + " | ".join(f"{op}: {t[op]*1000:7.1f} мс" for op in OPS))
                except Exception as exc:
                    ok = False
                    if verbose:
                        print(f"  ПОМИЛКА: {exc}")
                    break

            if not ok or not all(run_times[op] for op in OPS):
                continue

            agg = {op: statistics.median(run_times[op]) for op in OPS}
            results.append(BenchResult(engine=eng.name, n=n, op_total=agg))

    return results


def _fmt_us(us):
    """Гарно показати час у мікросекундах: великі значення переводимо в мс."""
    if us >= 1000:
        return f"{us/1000:.2f} мс"
    return f"{us:.1f} мкс"


def _fmt_ms(s):
    """Гарно показати час у секундах: маленькі - у мілісекундах."""
    if s >= 1.0:
        return f"{s:.3f} с"
    return f"{s*1000:.2f} мс"


def build_summary_table(results, op):
    """Будує таблицю для однієї операції: рядки - структури, стовпці - розміри N.

    У кожній клітинці показуємо одразу і загальний час, і час на одну
    операцію - так наочніше.
    """
    sizes = sorted({r.n for r in results})
    engines = sorted({r.engine for r in results})

    header = ["Структура"] + [f"N={n}" for n in sizes]
    rows = []
    for eng in engines:
        row = [eng]
        for n in sizes:
            entry = next((r for r in results if r.engine == eng and r.n == n), None)
            if entry is None:
                row.append("-")
            else:
                t_total = entry.op_total[op]
                t_per = entry.op_per_op_us[op]
                row.append(f"{_fmt_ms(t_total)} ({_fmt_us(t_per)}/оп)")
        rows.append(row)
    return header, rows


def render_ascii_table(header, rows):
    """Малює гарну ASCII-табличку з рамочкою - щоб було приємно дивитися в консолі."""
    cols = len(header)
    widths = [len(h) for h in header]
    for row in rows:
        for i in range(cols):
            widths[i] = max(widths[i], len(row[i]))

    def line(ch_left, ch_mid, ch_right, fill="-"):
        parts = [fill * (w + 2) for w in widths]
        return ch_left + ch_mid.join(parts) + ch_right

    def render_row(values):
        cells = [f" {values[i]:<{widths[i]}} " for i in range(cols)]
        return "|" + "|".join(cells) + "|"

    out = []
    out.append(line("+", "+", "+"))
    out.append(render_row(header))
    out.append(line("+", "+", "+", fill="="))
    for r in rows:
        out.append(render_row(r))
        out.append(line("+", "+", "+"))
    return "\n".join(out)


def save_csv(path, header, rows):
    """Зберігає таблицю як CSV - її легко відкрити в Excel/LibreOffice."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def save_raw_csv(path, results):
    """Зберігає всі сирі результати в одному CSV - на випадок, якщо хочеться
    самостійно покрутити їх у pandas/Excel."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["структура", "n", "операція", "загальний_час_с", "час_на_операцію_мкс", "операцій_за_сек"])
        for r in results:
            for op in OPS:
                if op not in r.op_total:
                    continue
                w.writerow([r.engine, r.n, op, f"{r.op_total[op]:.6f}", f"{r.op_per_op_us[op]:.3f}", f"{r.ops_per_sec[op]:.2f}"])


def _engines_in_order(results):
    """Повертає список структур у «правильному» порядку - щоб у легенді
    AVL завжди йшов першим, а SQLite - останнім."""
    preferred = ["AVL", "Splay", "RB", "B-дерево", "B+ дерево", "SQLite"]
    present = {r.engine for r in results}
    return [e for e in preferred if e in present]


def plot_lines_grid(results, out_path):
    """Сітка 2×2: 4 графіки часу від N - по одному на кожну операцію.

    Осі обидві логарифмічні: на лінійній шкалі дрібні значення зливаються
    в нуль, а нам цікаво, як саме часи ростуть зі збільшенням N.
    """
    sizes = sorted({r.n for r in results})
    engines = _engines_in_order(results)

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    fig.suptitle("Час виконання операцій залежно від обсягу даних N", fontsize=15, color=DARK["title"], fontweight="bold", y=0.995)

    for ax, op in zip(axes.flat, OPS):
        for eng in engines:
            ys = []
            xs = []
            for n in sizes:
                entry = next((r for r in results if r.engine == eng and r.n == n), None)
                if entry is None:
                    continue
                xs.append(n)
                ys.append(entry.op_total[op] * 1000)
            if xs:
                ax.plot(xs, ys, marker="o", label=eng, color=ENGINE_COLORS.get(eng, "#888"))

        ax.set_title(op)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("N (кількість записів)")
        ax.set_ylabel("час, мс (log)")
        ax.grid(True, which="both", alpha=0.5)

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=min(len(labels), 8), bbox_to_anchor=(0.5, -0.01), frameon=False)
    fig.tight_layout(rect=[0, 0.04, 1, 0.97])
    fig.savefig(out_path, bbox_inches="tight", facecolor=DARK["bg"])
    plt.close(fig)


def plot_lines_per_op(results, out_dir):
    """Окремий лінійний графік на кожну операцію: середній час однієї операції від N."""
    sizes = sorted({r.n for r in results})
    engines = _engines_in_order(results)

    for op in OPS:
        fig, ax = plt.subplots(figsize=(10, 6))
        for eng in engines:
            xs, ys = [], []
            for n in sizes:
                entry = next((r for r in results if r.engine == eng and r.n == n), None)
                if entry is None:
                    continue
                xs.append(n)
                ys.append(entry.op_per_op_us[op])
            if xs:
                ax.plot(xs, ys, marker="o", label=eng, color=ENGINE_COLORS.get(eng, "#888"))

        ax.set_title(f"Середній час однієї операції {op}")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("N (кількість записів)")
        ax.set_ylabel("час на операцію, мкс (log)")
        ax.grid(True, which="both", alpha=0.5)
        ax.legend(loc="best", ncol=2)
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, f"lines_{op.lower()}.png"), bbox_inches="tight", facecolor=DARK["bg"])
        plt.close(fig)


def plot_bars_per_op(results, out_dir):
    """Стовпчикова діаграма - порівняння всіх структур на найбільшому N.

    Найкраще видно «хто переможець» саме на максимальному об'ємі даних:
    на маленьких N усі працюють приблизно однаково. Стовпці сортуємо
    від найшвидшого до найповільнішого, а над кожним пишемо точне значення.
    """
    if not results:
        return
    n_max = max(r.n for r in results)
    engines = _engines_in_order(results)

    for op in OPS:
        vals = []
        labels = []
        colors = []
        for eng in engines:
            entry = next((r for r in results if r.engine == eng and r.n == n_max), None)
            if entry is None:
                continue
            vals.append(entry.op_per_op_us[op])
            labels.append(eng)
            colors.append(ENGINE_COLORS.get(eng, "#888"))

        if not vals:
            continue

        fig, ax = plt.subplots(figsize=(10, 6))
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        vals_s = [vals[i] for i in order]
        labels_s = [labels[i] for i in order]
        colors_s = [colors[i] for i in order]

        bars = ax.bar(labels_s, vals_s, color=colors_s, edgecolor=DARK["grid"], linewidth=1.5)
        ax.set_title(f"{op}: середній час однієї операції при N = {n_max}")
        ax.set_ylabel("час на операцію, мкс")
        ax.set_yscale("log")
        ax.grid(True, axis="y", which="both", alpha=0.5)

        for bar, v in zip(bars, vals_s):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), _fmt_us(v), ha="center", va="bottom", fontsize=9, color=DARK["text"])

        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, f"bars_{op.lower()}.png"), bbox_inches="tight", facecolor=DARK["bg"])
        plt.close(fig)


def parse_args():
    """Розбирає прапорці з командного рядка та повертає налаштування запуску."""
    p = argparse.ArgumentParser(description="Етап 3 - порівняльне дослідження дерев та СУБД.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--sizes", type=int, nargs="+", default=None, help="Список розмірів N (за замовчуванням: 1000 2500 5000 10000 25000 50000)")
    p.add_argument("--repeats", type=int, default=None, help="Скільки разів повторюємо кожне виконання - потім беремо медіану (за замовчуванням 1)")
    p.add_argument("--seed", type=int, default=42, help="Зерно генератора випадкових чисел - для відтворюваності результатів")
    p.add_argument("--quick", action="store_true", help="Швидка перевірка на малих N - корисно, щоб переконатися, що скрипт взагалі працює")
    p.add_argument("--output", default="results", help="Каталог, куди складати результати та графіки")

    p.add_argument("--no-avl", action="store_true", help="Не тестувати AVL-дерево")
    p.add_argument("--no-splay", action="store_true", help="Не тестувати splay-дерево")
    p.add_argument("--no-rb", action="store_true", help="Не тестувати червоно-чорне дерево")
    p.add_argument("--no-btree", action="store_true", help="Не тестувати B-дерево")
    p.add_argument("--no-bplus", action="store_true", help="Не тестувати B+ дерево")

    p.add_argument("--no-sqlite", action="store_true", help="Не порівнювати зі SQLite")

    p.add_argument("--btree-m", type=int, default=4, help="Параметр m (порядок) для B-дерева")
    p.add_argument("--bplus-m", type=int, default=4, help="Параметр m (порядок) для B+ дерева")

    return p.parse_args()


def build_engines(args):
    """За прапорцями з CLI збирає список двигунів, які треба прогнати."""
    engines = []

    if not args.no_avl:
        engines.append(TreeEngine("AVL", lambda: AVL_Tree()))
    if not args.no_splay:
        engines.append(TreeEngine("Splay", lambda: Splay_tree()))
    if not args.no_rb:
        engines.append(TreeEngine("RB", lambda: RBTree()))
    if not args.no_btree:
        m = args.btree_m
        engines.append(TreeEngine("B-дерево", lambda m=m: BTree(m=m)))
    if not args.no_bplus:
        m = args.bplus_m
        engines.append(TreeEngine("B+ дерево", lambda m=m: BPlusTree(m=m)))

    if not args.no_sqlite and HAS_SQLITE:
        engines.append(SQLiteEngine(in_memory=True))
    elif not args.no_sqlite:
        print("[i] SQLite недоступний у цьому Python - пропускаю.")

    return engines


def main():
    """Головна точка входу: розбирає аргументи, проганяє бенчмарк,
    зберігає таблиці та малює графіки."""
    args = parse_args()

    if args.quick:
        if args.sizes is None:
            args.sizes = [200, 500, 1000, 2000]
        if args.repeats is None:
            args.repeats = 2
        args.repeats = max(args.repeats, 2)
    else:
        if args.sizes is None:
            args.sizes = [1000, 2500, 5000, 10000, 25000, 50000]
        if args.repeats is None:
            args.repeats = 1

    setup_dark_style()

    engines = build_engines(args)
    if not engines:
        print("Не вибрано жодної структури - нема чого тестувати.")
        return 1

    out_dir = args.output
    plots_dir = os.path.join(out_dir, "plots")
    tables_dir = os.path.join(out_dir, "tables")
    os.makedirs(plots_dir, exist_ok=True)
    os.makedirs(tables_dir, exist_ok=True)

    print("=" * 72)
    print(" Етап 3: порівняльне дослідження")
    print("=" * 72)
    print(f" Розміри N    : {args.sizes}")
    print(f" Повторів     : {args.repeats}")
    print(f" Структури    : {[e.name for e in engines]}")
    print(f" Каталог      : {os.path.abspath(out_dir)}")
    print("-" * 72)

    t_start = time.perf_counter()
    results = run_benchmark(engines, sizes=args.sizes, repeats=args.repeats, seed=args.seed, verbose=True)
    elapsed = time.perf_counter() - t_start

    if not results:
        print("На жаль, не вдалося отримати жодного результату.")
        return 1

    save_raw_csv(os.path.join(out_dir, "raw_results.csv"), results)

    print()
    print("=" * 72)
    print(" Зведені таблиці (медіанний загальний час та середній час на операцію)")
    print("=" * 72)

    for op in OPS:
        header, rows = build_summary_table(results, op)
        ascii_tbl = render_ascii_table(header, rows)

        print()
        print(f" Операція: {op}")
        print(ascii_tbl)

        save_csv(os.path.join(tables_dir, f"summary_{op.lower()}.csv"), header, rows)

    print()
    print(" Малюю графіки ...")
    plot_lines_grid(results, os.path.join(plots_dir, "lines_all.png"))
    plot_lines_per_op(results, plots_dir)
    plot_bars_per_op(results, plots_dir)

    print()
    print("=" * 72)
    print(f" Готово за {elapsed:.2f} с.")
    print(f" Графіки    : {os.path.abspath(plots_dir)}")
    print(f" Таблиці    : {os.path.abspath(tables_dir)}")
    print(f" Сирі дані  : {os.path.abspath(os.path.join(out_dir, 'raw_results.csv'))}")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
