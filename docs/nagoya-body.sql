-- 名古屋市を対応機関として登録し、分類3件を付ける（管理画面 /admin/bodies の代わりに DB へ直接）
-- docker compose exec -T postgres psql -U fms -d fixmystreet < docs/nagoya-body.sql
INSERT INTO body (name) SELECT '名古屋市' WHERE NOT EXISTS (SELECT 1 FROM body WHERE name='名古屋市');
INSERT INTO body_areas (body_id, area_id) SELECT id, 989637 FROM body WHERE name='名古屋市' AND NOT EXISTS (SELECT 1 FROM body_areas WHERE area_id=989637);
INSERT INTO contacts (body_id, category, email, state, editor, whenedited, note)
SELECT b.id, c.category, 'doboku@example.org', 'confirmed', 'kit', now(), '初期登録'
FROM body b, (VALUES ('道路の穴・舗装の破損'),('不法投棄'),('街路灯の故障')) AS c(category)
WHERE b.name='名古屋市' AND NOT EXISTS (SELECT 1 FROM contacts x WHERE x.body_id=b.id AND x.category=c.category);
