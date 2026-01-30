# MySQLのOnline DDL機能について

MySQLのOnline DDLは、テーブル定義の変更をサービス稼働中に行える機能です。

## 主な特徴

- ALTER TABLE中もDMLを継続可能
- INPLACEアルゴリズムでテーブルコピーを回避
- ロック取得が最小限で済む

## 注意点

* メモリ使用量が増加する場合がある
* 大規模テーブルでは時間がかかる
+ バックアップとの整合性に注意

## コード例

```sql
ALTER TABLE users ADD COLUMN email VARCHAR(255), ALGORITHM=INPLACE, LOCK=NONE;
```

以上が基本的なOnline DDLの説明です。
