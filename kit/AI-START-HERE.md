# AIエージェントへ（このファイルを最初に読ませてください）

あなたはこれから、Docker が動くサーバー上に **FixMyStreet（道路の穴や不法投棄の通報プラットフォーム）** を日本語で構築し、利用者の市区町村で通報フォームが動くところまで進めます。利用者はプログラマーではありません。専門用語で確認を求めず、あなたが判断して進めてください。

## 進める順番

1. `01-構築手順書.md` を最初から最後まで読む
2. サーバーで `docker compose version` と空きメモリ・空きポートを確認する（手順書1章）。ポート 8000 が他で使われていたら `docker-compose.override.yml` で変える
3. `conf/general.yml-jp` の `BASE_URL`・`EMAIL_DOMAIN`・`CONTACT_EMAIL` を利用者の値にする（手順書2章）
4. `docker compose up -d` → コンテナ内で `locale-gen ja_JP.UTF-8` と `gettext-makemo` → `systemctl restart fixmystreet`（手順書3章）。**これをやらないと英語のままです**
5. `tools/find-area.sh <経度> <緯度>` で利用者の市区町村の area id を引き、`tools/nagoya-body.sql` の名前と id を差し替えて流す（手順書4章）。分類と通報先メールは利用者に聞く
6. ブラウザで `/report/new?latitude=<緯度>&longitude=<経度>` を開き、**分類が日本語で出て「次へ」まで進めることを画面で確認してから**完了報告する（手順書5章）
7. メール送信（SMTP）の設定は利用者のメールサーバー情報が要る。もらえない場合は「通報はDBに溜まるがメールは飛ばない」状態であることを明記して報告する

## 絶対に守ること

- `bin/createsuperuser` で作る管理者のパスワードを、報告文・チャットログに貼らない
- `/sys/fs/cgroup` のマウントと `cgroup: host` は削らない（コンテナ内の systemd が動かなくなる。落とし穴①）
- 「たぶん動く」で完了報告しない。通報フォームの画面と `docker compose ps` の実測で確認する
- 本家 FixMyStreet・mySociety のサポート窓口に、このキットの質問を送らない（非公式キットです）
