---
title: Automatic1111 positive prompt 設定
created: 2025-11-23
tags:
  - Automatic1111
  - Pony Diffusion
  - プロンプト
  - アニメ
  - 画像生成
summary: "Automatic1111のpositiveプロンプト設定について、Pony系モデルでの最適化を議論。スペルミス修正、冗長性の排除、`rating`タグの追加、アニメ顔を強調するための具体的なタグの追加など、改善案が提示された。"
source_provider: claude
file_id: 3a6b538ebe39
normalized: true
genre: other
topic: 画像生成プロンプト
---

### 初期プロンプトと問題点
Humanが設定した初期プロンプトは以下の通り。
```
score_9_up,score_9,score_8_up,score_8,score_7_up,score_7,aesthetic,masterpeace,perfect face,source_anime
```
Assistantは、スペルミス（`masterpeace` → `masterpiece`）、冗長性（score系タグの多さ）、`source_anime`のモデル依存性などを指摘。

### Pony系モデル向け推奨プロンプト
Pony系モデルの場合、以下のプロンプトが推奨される。
```
score_9, score_8_up, score_7_up, source_anime, masterpiece, best quality, perfect face
```
変更点として、スペルミス修正、`aesthetic`の削除、`best quality`の追加がある。

### Pony系モデルにおける重要ポイント
- **score系タグ**: Ponyの学習方法上重要だが、上位3つ程度で十分。
- **source_anime**: アニメ風を狙うなら必須。
- **rating系タグ**: `rating_safe`, `rating_questionable`, `rating_explicit` を検討。

### アニメ顔を強調するプロンプト
アニメ顔を強調するプロンプトの例。
```
score_9, score_8_up, score_7_up, source_anime, rating_safe, masterpiece, best quality, anime style, perfect anime face, detailed face
```
さらに強調する場合、`large eyes`, `expressive eyes`, `beautiful detailed eyes` などのタグを追加。

### アニメ顔の特徴と避けたい表現
- **アニメ顔の特徴**: `large eyes`, `expressive eyes`, `beautiful detailed eyes`, `anime nose`, `soft features`, `cel shading`
- **避けたい表現**: `realistic`, `photorealistic`, `3d`

### Negativeプロンプト
リアル寄りになる表現を避けるためのNegativeプロンプトの例。
```
realistic, 3d, photorealistic, ugly, bad anatomy, bad hands, bad face, poorly drawn face
```