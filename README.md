# miraisil-web

## /signs/ ページ（星座を選ぶ）

ハブアカウント(kyonounsei)のプロフィールリンク先。12星座から選んで
各星座の専用Instagramアカウント(kyonounsei_aries〜kyonounsei_pisces)
へ遷移するページ。

### クリック計測

タップ時に `https://miraisil-webhook.onrender.com/track-sign-click`
（dataunsei-automation リポジトリの line_webhook.py）へ非同期でPOSTし、
Supabaseの `sign_link_clicks` テーブル（sign, clicked_at）に記録される。
バックエンド側で星座キーをホワイトリスト検証しているため、自由文字列は
記録されない。

集計はSupabase SQL Editorで以下を実行:

```sql
-- 星座別クリック数（多い順）
SELECT sign, count(*) AS clicks
FROM sign_link_clicks
GROUP BY sign
ORDER BY clicks DESC;

-- 日別クリック数
SELECT date(clicked_at) AS day, count(*) AS clicks
FROM sign_link_clicks
GROUP BY day
ORDER BY day DESC;
```