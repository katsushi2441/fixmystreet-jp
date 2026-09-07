#!/usr/bin/env python3
"""gettext PO の未訳エントリをローカル gemma4（0.3・think:false）で日本語化する。
- プレースホルダ(%s %d %% %{x} {{x}} #{x} HTMLタグ &entity; URL 改行)を逐語保持。不一致は不採用
- 先頭/末尾の空白は原文に合わせて補正。複数形は ja（nplurals=1）なので msgstr[0] のみ
- 進捗は10バッチごとに保存（再実行で続きから）
使い方: translate_po_gemma.py <po> --domain fms|alaveteli [--limit N]
"""
import json, re, sys, time
import polib, requests
OLLAMA = "http://192.168.0.3:11434"; GEMMA = "gemma4:12b-it-qat"
PH = re.compile(r"%\{[^}]+\}|\{\{[^}]+\}\}|#\{[^}]+\}|%%|%\d*\$?[sd]|</?[a-zA-Z][^>]*>|&[a-zA-Z#0-9]+;|https?://\S+|\n")
SYS_COMMON = """出力はJSONのみ: {"items":[{"i":番号,"ja":"訳文"}]}
厳守事項:
- プレースホルダ・マークアップは一字も変えずそのまま残す: %s %d %% %{name} {{name}} #{name} などの変数、HTMLタグと属性、&ndash; などの実体参照、URL、改行(\\n)
- 原文の先頭・末尾の空白や句読点はそのまま残す
- 固有名詞・製品名は英語のまま（FixMyStreet, Alaveteli, mySociety, OpenStreetMap, Google, Bing, CSV, RSS, JSON, API など）
- 短いラベルは名詞形、文はですます調。UIとして自然な日本語にする（直訳調を避ける）
- 意味が分からない断片（記号だけ、1文字など）はそのまま返す"""
SYS = {
 "fms": "あなたは道路の穴・不法投棄・街灯故障などを自治体に通報するWebサービス「FixMyStreet」のUI文言の英日翻訳者です。英国の自治体向けの原文を、日本の自治体・住民に自然な日本語UI文言に翻訳してください。\n用語統一: report=通報 / problem=問題 / council=自治体 / body=対応機関 / category=分類 / update=更新（進捗の投稿） / alert=通知 / area=地域 / ward=区域 / contact=連絡先 / questionnaire=アンケート / staff=職員 / inspector=点検担当 / dashboard=ダッシュボード / superuser=管理者 / postcode=郵便番号 / photo=写真\n" + SYS_COMMON,
 "alaveteli": "あなたは情報公開請求（FOI）を行政機関にオンラインで行い、請求と回答を公開するWebサービス「Alaveteli」のUI文言の英日翻訳者です。原文（英国の情報公開制度）を、日本の情報公開制度に自然な日本語UI文言に翻訳してください。\n用語統一: request=請求（情報公開請求） / public authority=行政機関 / authority=機関 / requester=請求者 / response=回答 / outgoing message=送信メッセージ / incoming message=受信メッセージ / follow up=追加の連絡 / annotation=コメント / track=フォロー / batch request=一括請求 / pro=Pro（そのまま） / embargo=公開保留 / attachment=添付ファイル / classify=状態の分類 / successful=開示された / refused=不開示 / partially successful=一部開示 / awaiting response=回答待ち / overdue=期限超過 / user=利用者 / admin=管理者\n" + SYS_COMMON,
}
def tokens(s): return sorted(PH.findall(s))
def fix_ws(src, ja):
    lead = len(src) - len(src.lstrip(' ')); trail = len(src) - len(src.rstrip(' '))
    core = ja.strip(' ')
    return ' ' * lead + core + ' ' * trail
def translate_batch(sysmsg, items):
    src = json.dumps({"items": [{"i": i, "en": s} for i, s in items]}, ensure_ascii=False)
    r = requests.post(OLLAMA + "/api/chat", timeout=900, json={
        "model": GEMMA, "stream": False, "think": False, "format": "json",
        "options": {"temperature": 0.2, "num_predict": 4000, "num_ctx": 8192},
        "messages": [{"role": "system", "content": sysmsg}, {"role": "user", "content": src}]})
    r.raise_for_status()
    out = json.loads(r.json()["message"]["content"])
    return {int(x["i"]): str(x["ja"]) for x in out.get("items", []) if "i" in x and "ja" in x}
def main():
    path = sys.argv[1]; dom = sys.argv[sys.argv.index("--domain") + 1]
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 0
    po = polib.pofile(path)
    unt = [e for e in po if not e.translated() and not e.obsolete and e.msgid.strip()]
    if limit: unt = unt[:limit]
    print(f"未訳 {len(unt)} 件 model={GEMMA} domain={dom}", flush=True)
    ok = ng = 0; B = 8; t0 = time.time()
    for bi in range(0, len(unt), B):
        batch = unt[bi:bi + B]
        items = [(i, e.msgid) for i, e in enumerate(batch)]
        got = {}
        for attempt in range(2):
            try:
                got = translate_batch(SYS[dom], items); break
            except Exception as ex:
                print(f"  batch{bi//B}: 失敗 {str(ex)[:80]}（{attempt+1}回目）", flush=True); time.sleep(8)
        for i, e in enumerate(batch):
            ja = got.get(i)
            if not ja or not ja.strip(): ng += 1; continue
            ja = fix_ws(e.msgid, ja)
            if tokens(e.msgid) != tokens(ja): ng += 1; continue
            if e.msgid_plural: e.msgstr_plural = {0: ja}
            else: e.msgstr = ja
            if "fuzzy" in e.flags: e.flags.remove("fuzzy")
            ok += 1
        if (bi // B) % 10 == 0:
            po.save(path); print(f"  進捗 {bi+len(batch)}/{len(unt)} 採用{ok} 不採用{ng} {int(time.time()-t0)}s", flush=True)
    po.save(path); print(f"完了: 採用{ok} 不採用{ng} → {path}", flush=True)
if __name__ == "__main__": main()
