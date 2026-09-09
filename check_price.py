#!/usr/bin/env python3
"""サイト内のPremium価格表示が全ページで一致しているかを検査する。

■ なぜ要るか
2026-09-10 の値上げ（330→490）で、index.html・lp1・tokushoho が値上げ前から
980円のまま放置されていたことが分かった。実際の課金は330円だったので、
トップページと特定商取引法の表記が実価格と食い違ったまま数週間動いていた。
気づけなかった理由は2つある。

  (1) index.html・lp1 の価格は
      `月額</span><span class="price">980</span><span class="label">円（税込）`
      と数字がタグで分断されていて、「月額980」等の検索に引っかからない。
  (2) 素の「980」で検索すると CSS のブレークポイント（max-width:980px）や
      個人鑑定の 1,980円 に埋もれて、価格かどうか判別できない。

そこで価格を出す要素に data-price-jpy を付け、この検査で
「マーカーの数字」と「実際に表示される文字」と「全ページ間」の3つが
一致することを機械で確かめる。

■ 使い方
    python3 check_price.py            … ページ間の不一致だけを見る
    python3 check_price.py 490        … 490円であることも確かめる
不一致があれば終了コード1。値上げのときは、書き換えたあとに必ず実行すること。
金額の正はコード側の stripe_checkout.PREMIUM_PRICE_JPY（LINEの文言もそこを見る）。
Stripe上の実際の請求額はさらに別（Priceが持つ）ので、そちらも忘れず確認する。

■ 対象外
review/ は朝配信が毎日書き出す自動生成ページなので見ない（配信文面の写しであり、
次の配信で必ず更新される）。個人鑑定の 1,980円 と 無料プランの 0円 も対象外。
"""
import html
import re
import sys
from pathlib import Path

SKIP_DIRS = {".git", "review", "node_modules", "drafts", "output"}
# 個人鑑定(1,980円)・無料プラン(0円)は月額Premiumの価格ではない。
IGNORE = {"1,980", "1980", "0"}


def visible_text(src: str) -> str:
    """タグとscript/styleを落とした、実際に読める文字列。"""
    s = re.sub(r"<(script|style)\b.*?</\1>", " ", src, flags=re.S | re.I)
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", "", s)          # タグは詰めて消す（数字の分断を復元する）
    return html.unescape(re.sub(r"[ \t\r\f\v]+", " ", s))


def prices_in(text: str) -> set:
    """本文に出てくる月額価格（円）の集合。"""
    out = set()
    for m in re.finditer(r"月額\s*([0-9,]+)\s*円", text):
        if m.group(1) not in IGNORE:
            out.add(m.group(1).replace(",", ""))
    for m in re.finditer(r"¥\s*([0-9,]+)\s*(?:</?[^>]*>)?\s*/\s*月", text):
        if m.group(1) not in IGNORE:
            out.add(m.group(1).replace(",", ""))
    return out


def main() -> int:
    expect = None
    for a in sys.argv[1:]:
        if a.isdigit():
            expect = a
    root = Path(__file__).resolve().parent
    found, problems = {}, []
    for p in sorted(root.rglob("*.html")):
        if SKIP_DIRS & set(p.relative_to(root).parts):
            continue
        src = p.read_text(encoding="utf-8")
        rel = str(p.relative_to(root))
        markers = set(re.findall(r'data-price-jpy="([0-9]+)"', src))
        shown = prices_in(visible_text(src))
        if not markers and not shown:
            continue
        found[rel] = (markers, shown)
        # マーカーと表示のズレ（同じファイルの中で数字が二重管理になっている箇所）
        if markers and shown and markers != shown:
            problems.append(f"{rel}: data-price-jpy={sorted(markers)} と表示 {sorted(shown)} が違う")
        # マーカーがあるのに価格が読み取れない＝表示が壊れたか、書式が想定外に変わった。
        # ここを見逃すと「価格が消えたページ」を素通しする（実際に一度素通しした）。
        if markers and not shown:
            problems.append(f"{rel}: data-price-jpy={sorted(markers)} があるのに表示から価格を読み取れない")
        if shown and len(shown) > 1:
            problems.append(f"{rel}: 同じページに複数の価格 {sorted(shown)}")

    print(f"検査したページ {len(found)}件")
    for rel, (markers, shown) in found.items():
        m = "/".join(sorted(markers)) or "—"
        s = "/".join(sorted(shown)) or "—"
        print(f"  {rel:22s} マーカー={m:>6s}  表示={s:>6s}円")

    all_shown = set().union(*(s for _m, s in found.values())) if found else set()
    if len(all_shown) > 1:
        problems.append(f"ページ間で価格が不一致: {sorted(all_shown)}")
    if expect and all_shown - {expect}:
        problems.append(f"期待 {expect}円 と違う値がある: {sorted(all_shown - {expect})}")

    if problems:
        print("\n★ 不一致")
        for x in problems:
            print("   ", x)
        return 1
    print(f"\n一致しています（{'/'.join(sorted(all_shown)) or '価格表示なし'}円）"
          + ("" if expect else "　※ 引数に金額を渡すと絶対値も確かめます"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
